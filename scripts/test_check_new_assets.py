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

  def test_tracked_exception_only_allows_missing_external(self):
    """The index exception remains narrow and visible, with other fields required."""
    asset = {
      'id': 'coinbase-50-index',
      'about': {'en': 'A crypto index.'},
      'urls': {'Website': 'https://example.org/index'},
    }
    self.write_asset('coinbase-50-index', asset)
    self.run_git('add', '.')
    result = self.check()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn('https://github.com/tribulnation/catalogue/issues/152', result.stdout)
    asset['about'] = {'en': ' '}
    asset['urls'] = {}
    self.write_asset('coinbase-50-index', asset)
    result = self.check()
    self.assertEqual(result.returncode, 1)
    self.assertIn('about.en', result.stderr)
    self.assertIn('urls', result.stderr)
    self.assertNotIn('external must', result.stderr)
    self.assertTrue(
      any(
        error.startswith('external ')
        for error in metadata_errors(asset, asset_id='another-index')
      )
    )

  def test_invalid_base_is_an_error(self):
    """Missing Git history must fail rather than silently check zero additions."""
    result = self.check('missing-base')
    self.assertEqual(result.returncode, 2)
    self.assertIn('Cannot compare new assets', result.stderr)


if __name__ == '__main__':
  unittest.main()
