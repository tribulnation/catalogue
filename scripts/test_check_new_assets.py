"""Exercise the new-asset metadata guard against isolated Git repositories."""

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from check_new_assets import metadata_errors

SCRIPT = Path(__file__).with_name('check_new_assets.py').resolve()


class NewAssetMetadataTest(unittest.TestCase):
  """Cover PR additions, legacy exclusions and command-line failure behavior."""

  def setUp(self):
    """Create a committed legacy asset without contacting any remote."""
    self.folder = TemporaryDirectory()
    self.addCleanup(self.folder.cleanup)
    self.root = Path(self.folder.name)
    self.run_git('init', '--quiet')
    self.write_asset('legacy', {})
    self.run_git('add', '.')
    self.run_git(
      '-c',
      'user.name=Fixture',
      '-c',
      'user.email=fixture@example.invalid',
      'commit',
      '--quiet',
      '-m',
      'Baseline',
    )
    self.base = self.run_git('rev-parse', 'HEAD').strip()

  def run_git(self, *args: str) -> str:
    """Run Git in the fixture repository."""
    return subprocess.run(
      ['git', *args], cwd=self.root, check=True, capture_output=True, text=True
    ).stdout

  def write_asset(self, name: str, asset: object):
    """Write an asset fixture with the normal catalogue directory structure."""
    path = self.root / 'data' / 'assets' / f'{name}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asset), encoding='utf-8')

  def check(self, base: str | None = None) -> subprocess.CompletedProcess[str]:
    """Invoke the standalone script just as CI does."""
    return subprocess.run(
      [sys.executable, str(SCRIPT), '--base', base or self.base],
      cwd=self.root,
      capture_output=True,
      text=True,
    )

  def test_legacy_changes_do_not_block(self):
    """Existing incomplete assets remain outside this focused guard."""
    self.write_asset('legacy', {'about': {'en': ''}})
    result = self.check()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn('Checked 0 new assets', result.stdout)

  def test_valid_addition_passes(self):
    """A newly tracked asset with all metadata passes despite legacy gaps."""
    self.write_asset(
      'new',
      {
        'about': {'en': 'A project token.'},
        'urls': {'Website': 'https://example.org'},
        'external': {'coinmarketcap': '123'},
      },
    )
    self.run_git('add', '.')
    result = self.check()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn('Checked 1 new assets', result.stdout)

  def test_incomplete_addition_fails_with_paths_and_fields(self):
    """Report every missing field on an added asset and exit unsuccessfully."""
    self.write_asset(
      'new', {'about': {'en': '  '}, 'urls': {}, 'external': {'coinmarketcap': '\t'}}
    )
    self.run_git('add', '.')
    result = self.check()
    self.assertEqual(result.returncode, 1)
    for field in ['about.en', 'urls', 'external']:
      self.assertIn(f'data/assets/new.json: {field}', result.stderr)
    self.assertNotIn('legacy.json', result.stderr)

  def test_empty_or_wrongly_typed_fields_fail(self):
    """Nulls, wrong containers and whitespace cannot satisfy metadata requirements."""
    for value in [None, '', ' ', [], {}, {'': 'value'}, {'key': '\t'}, {'key': 123}]:
      with self.subTest(value=value):
        self.assertEqual(
          len(metadata_errors({'about': value, 'urls': value, 'external': value})), 3
        )

  def test_malformed_json_fails_cleanly(self):
    """Unreadable additions produce a file-specific message instead of a traceback."""
    path = self.root / 'data/assets/broken.json'
    path.write_text('{', encoding='utf-8')
    self.run_git('add', '.')
    result = self.check()
    self.assertEqual(result.returncode, 1)
    self.assertIn('data/assets/broken.json: cannot read asset JSON', result.stderr)
    self.assertNotIn('Traceback', result.stderr)

  def write_exceptions(self, exceptions: dict[str, str]):
    """Write the reviewed-exceptions file the script reads from the checked repo."""
    path = self.root / 'scripts' / 'external_id_exceptions.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(exceptions), encoding='utf-8')

  def crypto_asset(self, external: dict[str, str]) -> dict:
    return {
      'id': 'new',
      'category': 'crypto',
      'about': {'en': 'A project token.'},
      'urls': {'Website': 'https://example.org'},
      'external': external,
    }

  def test_crypto_needs_both_providers_accounted_for(self):
    """One provider ID is not enough for crypto; the other gap must be justified."""
    self.write_asset('new', self.crypto_asset({'coingecko': 'new-token'}))
    self.run_git('add', '.')
    result = self.check()
    self.assertEqual(result.returncode, 1)
    self.assertIn("external.coinmarketcap is missing", result.stderr)
    self.assertIn("'new:coinmarketcap'", result.stderr)
    self.assertNotIn('external.coingecko', result.stderr)

  def test_justified_gaps_pass_and_are_reported(self):
    """A token with no listing anywhere passes once each provider gap is explained."""
    self.write_asset('new', self.crypto_asset({}))
    self.write_exceptions({
      '_README': ['ignored'],
      'new:coingecko': 'Searched by contract; no listing.',
      'new:coinmarketcap': 'Searched by symbol; only unrelated tokens.',
    })
    self.run_git('add', '.')
    result = self.check()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn('no coinmarketcap listing - Searched by symbol', result.stdout)

  def test_mismatch_and_blank_entries_do_not_justify(self):
    """Three-part mismatch keys and blank reasons cannot stand in for a search."""
    self.write_asset('new', self.crypto_asset({}))
    self.write_exceptions({'new:coingecko:new-token': 'Renamed.', 'new:coinmarketcap': ' '})
    self.run_git('add', '.')
    result = self.check()
    self.assertEqual(result.returncode, 1)
    self.assertIn('external.coingecko is missing', result.stderr)
    self.assertIn('external.coinmarketcap is missing', result.stderr)

  def test_stale_justification_fails(self):
    """A justification must go once the provider ID it excused is added."""
    self.write_asset('new', self.crypto_asset({'coingecko': 'a', 'coinmarketcap': '1'}))
    self.write_exceptions({'new:coinmarketcap': 'No listing.'})
    self.run_git('add', '.')
    result = self.check()
    self.assertEqual(result.returncode, 1)
    self.assertIn('stale justification', result.stderr)

  def test_non_crypto_needs_one_id_or_justification(self):
    """Uncategorized records such as an index pass on any single justified gap."""
    asset = {
      'id': 'coinbase-50-index',
      'about': {'en': 'A crypto index.'},
      'urls': {'Website': 'https://example.org/index'},
    }
    self.assertTrue(any(e.startswith('external ') for e in metadata_errors(asset)))
    self.assertEqual(
      metadata_errors(asset, missing={'coinbase-50-index:coingecko': 'An index.'}), []
    )
    self.assertTrue(
      any(
        e.startswith('external ')
        for e in metadata_errors(asset, missing={'another-index:coingecko': 'An index.'})
      )
    )

  def test_invalid_base_is_an_error(self):
    """Missing Git history must fail rather than silently check zero additions."""
    result = self.check('missing-base')
    self.assertEqual(result.returncode, 2)
    self.assertIn('Cannot compare new assets', result.stderr)


if __name__ == '__main__':
  unittest.main()
