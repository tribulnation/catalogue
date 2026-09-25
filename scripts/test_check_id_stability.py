"""Exercise the id-stability guard against injected baselines, without the network."""

import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

from check_id_stability import ids_in_archive, main


def write_data(root: Path, assets: dict[str, dict], platforms: tuple[str, ...] = ('ethereum',)):
  """Write a minimal data folder."""
  (root / 'assets').mkdir(parents=True)
  (root / 'platforms').mkdir()
  for id, extra in assets.items():
    (root / 'assets' / f'{id}.json').write_text(json.dumps({'id': id, 'display_name': id, 'symbol': id.upper(), **extra}))
  for id in platforms:
    (root / 'platforms' / f'{id}.json').write_text(json.dumps({'display_name': id, 'kind': 'blockchain'}))


def baseline_zip(path: Path, assets: tuple[str, ...], platforms: tuple[str, ...] = ('ethereum',)):
  """Write a published-style data.zip listing the given ids."""
  with zipfile.ZipFile(path, 'w') as zf:
    for id in assets:
      zf.writestr(f'assets/{id}.json', '{}')
    for id in platforms:
      zf.writestr(f'platforms/{id}.json', '{}')
    zf.writestr('platforms/order.txt', '\n'.join(platforms))


class IdStabilityScriptTest(unittest.TestCase):
  """Removal fails, aliasing and additions pass."""

  def setUp(self):
    """Create a temp folder with a baseline archive of two assets."""
    folder = TemporaryDirectory()
    self.addCleanup(folder.cleanup)
    self.root = Path(folder.name)
    self.baseline = self.root / 'data.zip'
    baseline_zip(self.baseline, ('bitcoin', 'old-coin'))

  def run_check(self, assets: dict[str, dict], platforms: tuple[str, ...] = ('ethereum',)) -> int:
    """Run the script's main against a data folder with `assets`."""
    data = self.root / 'data'
    write_data(data, assets, platforms)
    return main(['--baseline', str(self.baseline), '--data', str(data)])

  def test_removed_asset_fails(self):
    """Deleting a published asset file fails."""
    self.assertEqual(self.run_check({'bitcoin': {}}), 1)

  def test_alias_passes(self):
    """Keeping the file as a `replaced_by` alias passes."""
    self.assertEqual(self.run_check({'bitcoin': {}, 'old-coin': {'replaced_by': 'bitcoin'}}), 0)

  def test_addition_passes(self):
    """New ids are free."""
    self.assertEqual(self.run_check({'bitcoin': {}, 'old-coin': {}, 'new-coin': {}}), 0)

  def test_removed_platform_fails(self):
    """Platform ids are stable too."""
    self.assertEqual(self.run_check({'bitcoin': {}, 'old-coin': {}}, platforms=('base',)), 1)

  def test_archive_ids(self):
    """Only `<kind folder>/<id>.json` entries count."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
      zf.writestr('assets/bitcoin.json', '{}')
      zf.writestr('platforms/order.txt', '')
      zf.writestr('instruments/spot/binance.json', '{}')
      zf.writestr('protocols/cctp.json', '{}')
    self.assertEqual(ids_in_archive(buffer.getvalue()), {'asset': {'bitcoin'}, 'platform': set(), 'protocol': {'cctp'}})


if __name__ == '__main__':
  unittest.main()
