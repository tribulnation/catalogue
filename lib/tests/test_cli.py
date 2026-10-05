"""`tn catalogue download`: extract, skip when unchanged, update, and refuse foreign folders."""

import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
import zipfile

from typer.testing import CliRunner

from tribulnation.catalogue.cli import app


def write_archive(path: Path, asset_id: str) -> str:
  """Write a minimal loadable `data.zip` and return its file:// URL."""
  buffer = io.BytesIO()
  with zipfile.ZipFile(buffer, 'w') as zf:
    zf.writestr(f'assets/{asset_id}.json', json.dumps({'id': asset_id, 'display_name': asset_id.title(), 'symbol': asset_id[:3].upper()}))
    zf.writestr('platforms/order.txt', '')
  path.write_bytes(buffer.getvalue())
  return path.as_uri()


class DownloadTest(unittest.TestCase):
  def setUp(self):
    self.tmp = TemporaryDirectory()
    self.root = Path(self.tmp.name)
    self.data = self.root / 'data'
    self.url = write_archive(self.root / 'data.zip', 'bitcoin')
    patch = mock.patch('tribulnation.catalogue.data.cache.DEFAULT_CACHE_DIR', self.root / 'cache')
    patch.start()
    self.addCleanup(patch.stop)
    self.addCleanup(self.tmp.cleanup)

  def download(self, *args: str):
    return CliRunner().invoke(app, ['download', *args, '--url', self.url])

  def test_extracts_into_folder(self):
    result = self.download(str(self.data))
    self.assertEqual(result.exit_code, 0, result.output)
    self.assertTrue((self.data / 'assets' / 'bitcoin.json').exists())

  def test_unchanged_archive_leaves_folder_alone(self):
    self.download(str(self.data))
    (self.data / 'local.txt').write_text('mine')
    result = self.download(str(self.data))
    self.assertEqual(result.exit_code, 0, result.output)
    self.assertIn('already up to date', result.output)
    self.assertTrue((self.data / 'local.txt').exists())

  def test_changed_archive_replaces_folder(self):
    self.download(str(self.data))
    write_archive(self.root / 'data.zip', 'ethereum')
    result = self.download(str(self.data))
    self.assertEqual(result.exit_code, 0, result.output)
    self.assertFalse((self.data / 'assets' / 'bitcoin.json').exists())
    self.assertTrue((self.data / 'assets' / 'ethereum.json').exists())
    self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['cache', 'data', 'data.zip'])

  def test_refresh_reextracts_unchanged_archive(self):
    self.download(str(self.data))
    (self.data / 'local.txt').write_text('mine')
    result = self.download(str(self.data), '--refresh')
    self.assertEqual(result.exit_code, 0, result.output)
    self.assertFalse((self.data / 'local.txt').exists())

  def test_without_path_only_refreshes_cache(self):
    result = self.download()
    self.assertEqual(result.exit_code, 0, result.output)
    self.assertTrue(any((self.root / 'cache').glob('*.zip')))
    self.assertFalse(self.data.exists())

  def test_unusable_first_download_fails_cleanly(self):
    (self.root / 'data.zip').write_bytes(b'not a zip')
    result = self.download(str(self.data))
    self.assertEqual(result.exit_code, 1)
    self.assertIn('Cannot download', result.output)
    self.assertFalse(self.data.exists())

  def test_refuses_foreign_folder(self):
    self.data.mkdir()
    (self.data / 'notes.txt').write_text('keep me')
    result = self.download(str(self.data))
    self.assertEqual(result.exit_code, 1)
    self.assertEqual((self.data / 'notes.txt').read_text(), 'keep me')

  def test_unusable_download_keeps_folder(self):
    self.download(str(self.data))
    (self.root / 'data.zip').write_bytes(b'not a zip')
    result = self.download(str(self.data))
    self.assertEqual(result.exit_code, 0, result.output)
    self.assertTrue((self.data / 'assets' / 'bitcoin.json').exists())


if __name__ == '__main__':
  unittest.main()
