import io
import os
import re
import shutil
import sys
import urllib.request
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from functools import cached_property
from pathlib import Path

from .schema import Asset, Platform, Spot, Perpetual, Debt, Pool, SpamAddress
from .cache import ArchiveCache, DEFAULT_URL, DEFAULT_MAX_AGE, DEFAULT_TIMEOUT

DEFAULT_CACHE = Path.home() / '.cache' / 'tribulnation' / 'catalogue'
"""Extraction folder used by versions up to 0.3.3 (the archive cache now lives next to it)."""

_EVM_ADDRESS = re.compile(r'^0x[0-9a-fA-F]{40}$')


def _download(url: str, dest: Path, *, silent: bool = False) -> None:
  """Download and extract the catalogue archive."""
  if not silent:
    print(f'Downloading catalogue from {url} ...', file=sys.stderr)
  with urllib.request.urlopen(url) as response:
    data = response.read()
  # Extract to a per-process temp dir then rename in, so concurrent
  # downloads don't corrupt each other's extractall with rmtree.
  dest.parent.mkdir(parents=True, exist_ok=True)
  tmp = dest.with_suffix(f'.{os.getpid()}.tmp')
  shutil.rmtree(tmp, ignore_errors=True)
  tmp.mkdir()
  with zipfile.ZipFile(io.BytesIO(data)) as zf:
    zf.extractall(tmp)
  shutil.rmtree(dest, ignore_errors=True)
  try:
    tmp.rename(dest)
  except OSError:
    shutil.rmtree(tmp, ignore_errors=True)


@dataclass(frozen=True)
class PerpetualInstrument:
  """A venue's perpetual contract with its assets resolved to current catalogue ids."""
  platform: str
  id: str
  """Venue instrument id, e.g. `BTC` or `xyz:TSLA` on hyperliquid, `BTC-USD` on dydx"""
  base: str
  """Base asset id"""
  quote: str
  """Quote asset id"""
  settlement: str
  """Settlement asset id"""
  multiplier: Decimal
  """Units of `base` per contract unit (1 unless the venue scales it, e.g. `kPEPE`)"""
  delisted: bool


@dataclass(frozen=True)
class DebtInstrument:
  """A debt token whose balance is owed `asset`, with the asset resolved to its current id."""
  platform: str
  id: str
  """Debt token key (EIP-55 contract address on EVM chains)"""
  asset: str
  """Asset id owed"""
  name: str


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
  digest: str | None = None
  """sha256 of the loaded `data.zip`; None when loaded from a folder"""
  loaded_at: datetime | None = None
  """When the data was loaded from the cached archive; None when loaded from a folder"""
  cache: ArchiveCache | None = field(default=None, repr=False, compare=False)
  """The archive cache this catalogue came from, used by `maybe_refresh`"""

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
    max_age: timedelta = DEFAULT_MAX_AGE,
    cache_dir: Path | str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
  ) -> 'Catalogue':
    """Load the catalogue.

    Without `path`, the published `data.zip` is kept in a local cache. A cached copy
    checked less than `max_age` ago is used as-is; otherwise one conditional request
    (`ETag` / `Last-Modified`) asks whether it changed, and the archive is downloaded
    again only then. A download replaces the cached copy only once it loads. When the
    site is unreachable the last good copy is used and a warning is logged; only a
    first run with no cached copy raises.

    Args:
      path: Local data folder. An existing folder is read as-is and never touches the
        network (unless `refresh`); a missing one is downloaded into, as in earlier versions.
      refresh: Download unconditionally, ignoring the cached copy's validators.
      silent: Suppress the download message.
      url: Archive URL to download from. Defaults to the public catalogue.
      max_age: How long a check stays valid before the next conditional request.
      cache_dir: Cache folder for the archive; `~/.cache/tribulnation` by default.
      timeout: Network timeout in seconds.

    Raises:
      urllib.error.URLError: The site is unreachable and there is no cached copy.
    """
    from . import load
    if path is not None:
      path = Path(path)
      if refresh or not path.exists():
        _download(url, path, silent=silent)
      return load.all(path)
    cache = ArchiveCache(url=url, folder=cache_dir, max_age=max_age, timeout=timeout, silent=silent)
    return cache.load(force=refresh)

  def maybe_refresh(self) -> 'Catalogue':
    """The current catalogue: `self` unless `max_age` elapsed and the published archive changed.

    Cheap to call often (e.g. daily or per request): it only reads the cache sidecar until
    `max_age` has elapsed, then sends one conditional request. Catalogues loaded from a
    folder always return `self`. Network errors never raise; the last good copy stays.
    """
    if self.cache is None:
      return self
    return self.cache.load(self)

  def refresh(self) -> 'Catalogue':
    """Like `maybe_refresh`, but sends the conditional request regardless of `max_age`."""
    if self.cache is None:
      return self
    return self.cache.load(self, check=True)

  def is_evm(self, platform: str) -> bool:
    """Whether `platform` is an EVM blockchain, whose translation keys are contract addresses."""
    p = self.platforms.get(platform)
    return p is not None and p['kind'] == 'blockchain' and p.get('category') == 'evm'

  @cached_property
  def _evm_keys(self) -> dict[str, dict[str, str]]:
    """`platform -> lowercased address -> stored (checksummed) key` over EVM translations and debt tokens."""
    index: dict[str, dict[str, str]] = {}
    for source in (self.asset_translations, self.debt_instruments):
      for platform, entries in source.items():
        if self.is_evm(platform):
          index.setdefault(platform, {}).update((key.lower(), key) for key in entries)
    return index

  def translation_key(self, platform: str, raw_id: str | int) -> str:
    """Normalise a native id into the key used by `asset_translations[platform]` and `debt_instruments[platform]`.

    - EVM chains: any casing of a contract address maps to the stored EIP-55 form, and
      any casing of `native` to `native`.
    - Hyperliquid spot: the token index, as `int` or `str`.
    - Everything else (CEX and dYdX symbols, Solana/Tron addresses): exact, case-sensitive.
    """
    key = str(raw_id)
    if self.is_evm(platform):
      if key.lower() == 'native':
        return 'native'
      if _EVM_ADDRESS.match(key):
        return self._evm_keys.get(platform, {}).get(key.lower(), key)
    return key

  def canonical_id(self, asset_id: str) -> str:
    """Follow `replaced_by` aliases to the asset id currently in use."""
    seen = {asset_id}
    while (asset := self.assets.get(asset_id)) is not None and (target := asset.get('replaced_by')) is not None:
      if target in seen:
        break
      seen.add(target)
      asset_id = target
    return asset_id

  def asset(self, asset_id: str) -> Asset | None:
    """The asset record for `asset_id`, following `replaced_by` aliases."""
    return self.assets.get(self.canonical_id(asset_id))

  def asset_for(self, platform: str, raw_id: str | int) -> str | None:
    """The catalogue asset id of a platform-native asset, or None when it is not translated.

    Args:
      platform: Catalogue platform id, e.g. `hyperliquid`, `ethereum`, `arbitrum`, `bitget`, `dydx`.
      raw_id: Native id: the spot token index on hyperliquid, the contract address or `native`
        on EVM chains, the venue symbol on CEXs and dYdX.

    Examples:
      >>> catalogue.asset_for('hyperliquid', 150)
      'hyperliquid'
      >>> catalogue.asset_for('arbitrum', '0xaf88d065e77c8cc2239327c5edb3a432268e5831')
      'usd-coin'
    """
    translations = self.asset_translations.get(platform)
    if translations is None:
      return None
    asset_id = translations.get(self.translation_key(platform, raw_id))
    return self.canonical_id(asset_id) if asset_id is not None else None

  def perpetual_for(self, platform: str, id: str) -> PerpetualInstrument | None:
    """A perpetual instrument with its assets resolved, or None when it is not catalogued.

    Args:
      platform: Catalogue platform id, e.g. `hyperliquid` or `dydx`.
      id: Venue instrument id: the `meta.universe` coin on hyperliquid (`dex:COIN` for HIP-3),
        the ticker on dYdX (`BTC-USD`). Case-sensitive.
    """
    instrument = self.perpetual_instruments.get(platform, {}).get(id)
    if instrument is None:
      return None
    return PerpetualInstrument(
      platform=platform, id=id,
      base=self.canonical_id(instrument['base']),
      quote=self.canonical_id(instrument['quote']),
      settlement=self.canonical_id(instrument['settlement']),
      multiplier=Decimal(instrument.get('multiplier', 1)),
      delisted=instrument.get('delisted', False),
    )

  def debt_for(self, platform: str, raw_id: str) -> DebtInstrument | None:
    """A debt token (e.g. an Aave `variableDebt…` token) with its underlying asset, or None.

    Args:
      platform: Catalogue platform id, e.g. `ethereum`.
      raw_id: The debt token's contract address, in any casing.
    """
    debt = self.debt_instruments.get(platform, {}).get(self.translation_key(platform, raw_id))
    if debt is None:
      return None
    return DebtInstrument(platform=platform, id=self.translation_key(platform, raw_id), asset=self.canonical_id(debt['asset']), name=debt['name'])

  def network_for(self, platform: str, raw_network: str) -> str | None:
    """The catalogue platform id of a venue's network code (e.g. bybit `BSC (BEP20)`), or None."""
    return self.network_translations.get(platform, {}).get(raw_network)
