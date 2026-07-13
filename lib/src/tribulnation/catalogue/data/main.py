import io
import shutil
import sys
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .schema import Asset, Platform, Spot, Perpetual, Debt, Pool, SpamAddress

DEFAULT_URL = 'https://catalogue.tribulnation.com/data.zip'
DEFAULT_CACHE = Path.home() / '.cache' / 'tribulnation' / 'catalogue'


def _download(url: str, dest: Path, *, silent: bool = False) -> None:
  if not silent:
    print(f'Downloading catalogue from {url} ...', file=sys.stderr)
  with urllib.request.urlopen(url) as response:
    data = response.read()
  if dest.exists():
    shutil.rmtree(dest)
  dest.mkdir(parents=True)
  with zipfile.ZipFile(io.BytesIO(data)) as zf:
    zf.extractall(dest)


@dataclass
class Catalogue:
  assets: dict[str, Asset]
  platforms: dict[str, Platform]
  platforms_order: list[str]
  network_translations: dict[str, dict[str, str]]
  """`platform id -> platform-specific id -> network id`"""
  asset_translations: dict[str, dict[str, str]]
  """`platform id -> platform-specific id -> asset id`"""
  spot_instruments: dict[str, dict[str, Spot]]
  """`platform id -> instrument id -> spot instrument`"""
  perpetual_instruments: dict[str, dict[str, Perpetual]]
  """`platform id -> instrument id -> perpetual instrument`"""
  debt_instruments: dict[str, dict[str, Debt]]
  """`platform id -> instrument id -> debt instrument`"""
  pools: dict[str, dict[str, Pool]]
  """`platform id -> instrument id -> pool`"""
  spam: dict[str, dict[str, SpamAddress]]
  """`platform id -> address -> spam address`"""

  @property
  def ordered_platforms(self):
    for platform in self.platforms_order:
      yield platform, self.platforms[platform]

  @property
  def blockchains(self):
    return {id: p for id, p in self.platforms.items() if p['kind'] == 'blockchain'}

  @property
  def cexs(self):
    return {id: p for id, p in self.platforms.items() if p['kind'] == 'cex'}

  @property
  def dexs(self):
    return {id: p for id, p in self.platforms.items() if p['kind'] == 'dex'}

  @staticmethod
  def load(
    path: Path | str | None = None,
    *,
    refresh: bool = False,
    silent: bool = False,
    url: str = DEFAULT_URL,
  ) -> 'Catalogue':
    """Load the catalogue.

    Args:
      path: Local folder to load from directly. If omitted, uses `~/.cache/tribulnation/catalogue`.
      refresh: Re-download even if a cached copy exists.
      silent: Suppress the download progress message.
      url: Archive URL to download from. Defaults to the public catalogue.
    """
    from . import load
    path = Path(path or DEFAULT_CACHE)
    if refresh or not path.exists():
      _download(url, path, silent=silent)
    return load.all(path)
