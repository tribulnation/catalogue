"""The archive cache behind `Catalogue.load()`: conditional refresh, last good copy, digest."""

from datetime import timedelta
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest
import urllib.error
import zipfile

from tribulnation.catalogue import Catalogue


def archive(*asset_ids: str, platform_kind: str = 'cex') -> bytes:
  """A minimal `data.zip` with the given assets and one platform."""
  buffer = io.BytesIO()
  with zipfile.ZipFile(buffer, 'w') as zf:
    for id in asset_ids:
      zf.writestr(f'assets/{id}.json', json.dumps({'id': id, 'display_name': id.title(), 'symbol': id[:3].upper()}))
    zf.writestr('platforms/venue.json', json.dumps({'display_name': 'Venue', 'kind': platform_kind}))
    zf.writestr('platforms/order.txt', 'venue\n')
    zf.writestr('asset_translations/venue.json', json.dumps({'BTC': asset_ids[0]}))
  return buffer.getvalue()


class Server:
  """A local archive server that honours `If-None-Match` and counts full downloads."""

  def __init__(self, body: bytes):
    """Serve `body` on an ephemeral port."""
    self.body = body
    self.requests = 0
    self.downloads = 0
    self.status = 200
    server = self

    class Handler(BaseHTTPRequestHandler):
      """Serve the current body with a content-hash ETag."""

      def do_GET(self):
        """Answer 304, the body, or the configured error status."""
        server.requests += 1
        etag = f'"{hashlib.md5(server.body).hexdigest()}"'
        if server.status != 200:
          self.send_error(server.status)
          return
        if self.headers.get('If-None-Match') == etag:
          self.send_response(304)
          self.send_header('ETag', etag)
          self.end_headers()
          return
        server.downloads += 1
        self.send_response(200)
        self.send_header('ETag', etag)
        self.send_header('Content-Length', str(len(server.body)))
        self.end_headers()
        self.wfile.write(server.body)

      def log_message(self, format, *args):
        """Keep test output quiet."""

    self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    self.url = f'http://127.0.0.1:{self.httpd.server_address[1]}/data.zip'
    self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
    self.thread.start()

  def stop(self):
    """Shut the server down so connections are refused."""
    self.httpd.shutdown()
    self.httpd.server_close()


class ArchiveCacheTest(unittest.TestCase):
  """Refresh policy of the default (no `path`) load."""

  def setUp(self):
    """Start a server and an empty cache folder."""
    folder = TemporaryDirectory()
    self.addCleanup(folder.cleanup)
    self.cache_dir = Path(folder.name)
    self.v1 = archive('bitcoin')
    self.server = Server(self.v1)
    self.addCleanup(self.server.stop)

  def load(self, **kwargs) -> Catalogue:
    """Load through the cache against the local server."""
    kwargs.setdefault('max_age', timedelta(days=1))
    return Catalogue.load(url=self.server.url, cache_dir=self.cache_dir, silent=True, **kwargs)

  def test_first_load_downloads_and_exposes_digest(self):
    """A first load downloads, caches the archive and exposes its sha256."""
    catalogue = self.load()
    self.assertEqual(set(catalogue.assets), {'bitcoin'})
    self.assertEqual(catalogue.digest, hashlib.sha256(self.v1).hexdigest())
    self.assertIsNotNone(catalogue.loaded_at)
    self.assertEqual(self.server.downloads, 1)
    self.assertEqual(catalogue.asset_for('venue', 'BTC'), 'bitcoin')

  def test_fresh_cache_skips_network(self):
    """Within `max_age` no request is sent."""
    self.load()
    self.load()
    self.assertEqual(self.server.requests, 1)

  def test_stale_cache_sends_conditional_request(self):
    """After `max_age`, an unchanged archive costs one 304 and no download."""
    first = self.load()
    second = self.load(max_age=timedelta(0))
    self.assertEqual((self.server.requests, self.server.downloads), (2, 1))
    self.assertEqual(second.digest, first.digest)

  def test_maybe_refresh_reuses_unchanged(self):
    """`maybe_refresh` returns the same object while the data is unchanged."""
    catalogue = self.load(max_age=timedelta(0))
    self.assertIs(catalogue.maybe_refresh(), catalogue)
    self.assertIs(catalogue.refresh(), catalogue)
    self.assertEqual(self.server.downloads, 1)

  def test_maybe_refresh_picks_up_change(self):
    """A changed archive is downloaded once and replaces the cached copy."""
    catalogue = self.load(max_age=timedelta(0))
    self.server.body = archive('bitcoin', 'ethereum')
    updated = catalogue.maybe_refresh()
    self.assertIsNot(updated, catalogue)
    self.assertEqual(set(updated.assets), {'bitcoin', 'ethereum'})
    self.assertNotEqual(updated.digest, catalogue.digest)
    self.assertEqual(self.server.downloads, 2)
    self.assertEqual((self.cache_dir / next(p.name for p in self.cache_dir.glob('*.zip'))).read_bytes(), self.server.body)

  def test_fresh_check_is_not_repeated(self):
    """`maybe_refresh` within `max_age` does not send a request."""
    catalogue = self.load()
    catalogue.maybe_refresh()
    self.assertEqual(self.server.requests, 1)

  def test_outage_keeps_last_good_copy(self):
    """With the site down, a cached copy is used and a warning logged instead of raising."""
    catalogue = self.load(max_age=timedelta(0))
    self.server.stop()
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      again = self.load(max_age=timedelta(0))
    self.assertEqual(again.digest, catalogue.digest)
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      self.assertIs(catalogue.refresh(), catalogue)

  def test_server_error_keeps_last_good_copy(self):
    """An HTTP error is handled like an outage."""
    catalogue = self.load(max_age=timedelta(0))
    self.server.status = 503
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      self.assertIs(catalogue.refresh(), catalogue)

  def test_unloadable_download_keeps_last_good_copy(self):
    """A download that does not load never replaces the cached copy."""
    catalogue = self.load(max_age=timedelta(0))
    self.server.body = b'not a zip'
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      self.assertIs(catalogue.refresh(), catalogue)
    self.assertEqual(self.load().digest, catalogue.digest)

  def test_invalid_records_are_skipped(self):
    """A record the installed schema does not understand is skipped, not fatal."""
    self.server.body = archive('bitcoin', platform_kind='future-kind')
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      catalogue = self.load()
    self.assertEqual(set(catalogue.assets), {'bitcoin'})
    self.assertEqual(catalogue.platforms, {})

  def test_no_cache_and_no_site_raises(self):
    """Without a cached copy an outage is an error."""
    self.server.stop()
    with self.assertRaises(urllib.error.URLError):
      self.load()

  def test_refresh_flag_downloads_unconditionally(self):
    """`refresh=True` ignores the validators."""
    self.load()
    self.load(refresh=True)
    self.assertEqual(self.server.downloads, 2)


class ExplicitPathTest(unittest.TestCase):
  """An explicit existing folder is read locally."""

  def test_folder_has_no_digest_and_never_refreshes(self):
    """Folder loads carry no digest and `maybe_refresh` is a no-op."""
    with TemporaryDirectory() as folder:
      with zipfile.ZipFile(io.BytesIO(archive('bitcoin'))) as zf:
        zf.extractall(folder)
      catalogue = Catalogue.load(folder, url='http://127.0.0.1:9/unreachable.zip')
      self.assertEqual(set(catalogue.assets), {'bitcoin'})
      self.assertIsNone(catalogue.digest)
      self.assertIs(catalogue.maybe_refresh(), catalogue)


if __name__ == '__main__':
  unittest.main()
