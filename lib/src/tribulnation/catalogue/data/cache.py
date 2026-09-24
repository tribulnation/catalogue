"""Local cache of the published `data.zip`, kept fresh with conditional requests.

The archive is stored as-is next to a small JSON sidecar with its HTTP validators
(`ETag`, `Last-Modified`) and the time it was last checked. A check older than
`max_age` sends one conditional request; the archive is only downloaded again when
the server says it changed, only replaces the cached copy once it loads, and the
last good copy keeps serving when the site is unreachable.
"""

import hashlib
import json
import logging
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING
from typing_extensions import NotRequired, TypedDict

if TYPE_CHECKING:
  from .main import Catalogue

DEFAULT_URL = 'https://catalogue.tribulnation.com/data.zip'
DEFAULT_CACHE_DIR = Path.home() / '.cache' / 'tribulnation'
DEFAULT_MAX_AGE = timedelta(days=1)
DEFAULT_TIMEOUT = 10.0

logger = logging.getLogger('tribulnation.catalogue')


class CacheMeta(TypedDict):
  """Sidecar of the cached archive."""
  url: str
  sha256: str
  """Digest of the cached `data.zip`"""
  checked_at: str
  """ISO timestamp of the last successful check against `url`"""
  etag: NotRequired[str]
  last_modified: NotRequired[str]


def sha256(data: bytes) -> str:
  """Hex sha256 digest of `data`."""
  return hashlib.sha256(data).hexdigest()


def now() -> datetime:
  """Current UTC time."""
  return datetime.now(timezone.utc)


def write_atomic(path: Path, data: bytes):
  """Write `data` to `path` through a per-process temp file and an atomic rename."""
  path.parent.mkdir(parents=True, exist_ok=True)
  tmp = path.with_name(f'{path.name}.{os.getpid()}.tmp')
  tmp.write_bytes(data)
  os.replace(tmp, path)


class ArchiveCache:
  """The cached `data.zip` of one URL, and the policy that keeps it fresh."""

  def __init__(
    self, *, url: str = DEFAULT_URL, folder: Path | str | None = None,
    max_age: timedelta = DEFAULT_MAX_AGE, timeout: float = DEFAULT_TIMEOUT, silent: bool = False,
  ):
    """
    Args:
      url: Archive URL.
      folder: Cache folder; `~/.cache/tribulnation` by default.
      max_age: How long a successful check stays valid before the next conditional request.
      timeout: Network timeout in seconds.
      silent: Suppress the download message on stderr.
    """
    self.url = url
    self.folder = Path(folder) if folder is not None else DEFAULT_CACHE_DIR
    self.max_age = max_age
    self.timeout = timeout
    self.silent = silent
    name = 'catalogue' if url == DEFAULT_URL else f'catalogue-{sha256(url.encode())[:12]}'
    self.archive_path = self.folder / f'{name}.zip'
    self.meta_path = self.folder / f'{name}.zip.json'

  def read_meta(self) -> CacheMeta | None:
    """The sidecar, or None when missing, unreadable, or for another URL."""
    try:
      meta: CacheMeta = json.loads(self.meta_path.read_bytes())
    except (OSError, ValueError):
      return None
    if not isinstance(meta, dict) or meta.get('url') != self.url:
      return None
    return meta

  def read_archive(self) -> bytes | None:
    """The cached archive bytes, or None when there is no cached copy."""
    try:
      return self.archive_path.read_bytes()
    except OSError:
      return None

  def is_fresh(self, meta: CacheMeta) -> bool:
    """Whether the last check is recent enough to skip the network."""
    try:
      checked_at = datetime.fromisoformat(meta['checked_at'])
    except (KeyError, ValueError):
      return False
    return now() - checked_at < self.max_age

  def write_meta(self, meta: CacheMeta):
    """Atomically replace the sidecar."""
    write_atomic(self.meta_path, json.dumps(meta, indent=2).encode())

  def fetch(self, meta: CacheMeta | None) -> tuple[bytes | None, CacheMeta]:
    """Request the archive, conditionally when `meta` carries validators.

    Returns:
      `(body, meta)`: `body` is None when the server answered 304 Not Modified; `meta`
      holds the validators to store (its `sha256` is filled in by the caller).

    Raises:
      urllib.error.URLError, OSError: The request failed.
    """
    request = urllib.request.Request(self.url)
    if meta is not None:
      if (etag := meta.get('etag')) is not None:
        request.add_header('If-None-Match', etag)
      if (last_modified := meta.get('last_modified')) is not None:
        request.add_header('If-Modified-Since', last_modified)
    checked = CacheMeta(url=self.url, sha256='', checked_at=now().isoformat())
    try:
      with urllib.request.urlopen(request, timeout=self.timeout) as response:
        if not self.silent:
          print(f'Downloading catalogue from {self.url} ...', file=sys.stderr)
        body: bytes = response.read()
        headers = response.headers
    except urllib.error.HTTPError as e:
      if e.code != 304 or meta is None:
        raise
      return None, {**meta, 'checked_at': checked['checked_at']}
    if (etag := headers.get('ETag')) is not None:
      checked['etag'] = etag
    if (last_modified := headers.get('Last-Modified')) is not None:
      checked['last_modified'] = last_modified
    return body, checked

  def load(self, current: 'Catalogue | None' = None, *, check: bool = False, force: bool = False) -> 'Catalogue':
    """Return the up-to-date catalogue; `current` itself when its data did not change.

    Args:
      current: The catalogue loaded earlier from this cache, reused when unchanged.
      check: Send the conditional request even if the last check is younger than `max_age`.
      force: Download unconditionally (no validators), replacing the cached copy if it loads.

    Raises:
      urllib.error.URLError, OSError: The site is unreachable and there is no cached copy.
      pydantic.ValidationError, zipfile.BadZipFile: The download is unusable and there is no cached copy.
    """
    meta = self.read_meta()
    cached = self.read_archive()
    if cached is not None and meta is not None and not (check or force) and self.is_fresh(meta):
      return self.from_bytes(cached, current)
    try:
      body, checked = self.fetch(meta if cached is not None and not force else None)
    except (urllib.error.URLError, OSError) as e:
      if cached is None:
        raise
      logger.warning('Catalogue refresh from %s failed (%s); using the cached copy', self.url, e)
      return self.from_bytes(cached, current)
    if body is None:
      assert cached is not None
      self.write_meta(checked)
      return self.from_bytes(cached, current)
    digest = sha256(body)
    checked['sha256'] = digest
    if cached is not None and digest == sha256(cached):
      self.write_meta(checked)
      return self.from_bytes(cached, current)
    try:
      catalogue = self.from_bytes(body, None)
    except Exception as e:
      if cached is None:
        raise
      logger.warning('Catalogue download from %s does not load (%s); keeping the cached copy', self.url, e)
      if meta is not None:
        self.write_meta({**meta, 'checked_at': checked['checked_at']})
      return self.from_bytes(cached, current)
    write_atomic(self.archive_path, body)
    self.write_meta(checked)
    return catalogue

  def from_bytes(self, data: bytes, current: 'Catalogue | None') -> 'Catalogue':
    """Load archive bytes, reusing `current` when it holds the same digest."""
    from . import load
    digest = sha256(data)
    if current is not None and current.digest == digest:
      return current
    catalogue = load.archive(data, skip_invalid=True)
    if not catalogue.assets:
      raise ValueError('archive has no assets')
    catalogue.digest = digest
    catalogue.loaded_at = now()
    catalogue.cache = self
    return catalogue
