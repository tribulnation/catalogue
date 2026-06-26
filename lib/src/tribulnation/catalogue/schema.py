from typing_extensions import TypedDict, NotRequired, Literal, Mapping, Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

Locale = Literal['ca', 'es', 'en']
Translations = Mapping[Locale, str]

class Spot(TypedDict):
  exchange: NotRequired[str]
  """Exchange ID (for TradingSDK)"""
  base: str
  """Base asset ID"""
  quote: str
  """Quote asset ID"""

class Perpetual(TypedDict):
  exchange: NotRequired[str]
  """Exchange ID (for TradingSDK)"""
  base: str
  """Base asset ID"""
  quote: str
  """Quote asset ID"""
  settlement: str
  """Settlement asset ID"""

class Debt(TypedDict):
  asset: str
  """Underlying asset ID"""
  name: str

class Collateral(TypedDict):
  asset: str
  """Underlying asset ID"""
  name: str

class Pool(TypedDict):
  assets: list[str]
  """List of asset IDs"""
  name: str
  """Pool name"""

class SpamAddress(TypedDict, total=False):
  reason: str
  source: str
  reported_at: datetime

class ExternalIds(TypedDict, total=False):
  coingecko: str

class Asset(TypedDict):
  display_name: str
  symbol: str
  about: NotRequired[Translations]
  tags: NotRequired[list[str]]
  urls: NotRequired[dict[str, str]]
  icon: NotRequired[str]
  external: NotRequired[ExternalIds]

class BasePlatform(TypedDict):
  display_name: str
  about: NotRequired[Translations]
  urls: NotRequired[dict[str, str]]
  icon: NotRequired[str]

class CexPlatform(BasePlatform):
  kind: Literal['cex']

class DexPlatform(BasePlatform):
  kind: Literal['dex']

BlockchainCategory = Literal['evm']
BlockchainNamespace = Literal['bip122', 'cosmos', 'eip155', 'solana']

class Blockchain(BasePlatform):
  kind: Literal['blockchain']
  native_asset: NotRequired[str]
  category: NotRequired[BlockchainCategory]
  chain_id: NotRequired[int | str]
  namespace: NotRequired[BlockchainNamespace]

Platform = CexPlatform | DexPlatform | Blockchain

@dataclass
class Catalogue:
  assets: dict[str, Asset]
  platforms: dict[str, Platform]
  platforms_order: list[str]
  network_translations: dict[str, dict[str, str]]
  """`platform id -> platform-specific id -> platform id`"""
  asset_translations: dict[str, dict[str, str]]
  """`platform id -> platform-specific id -> asset id`"""
  spot_instruments: dict[str, dict[str, Spot]]
  """`platform id -> platform-specific id -> spot instrument`"""
  perpetual_instruments: dict[str, dict[str, Perpetual]]
  """`platform id -> platform-specific id -> perpetual instrument`"""
  debt_instruments: dict[str, dict[str, Debt]]
  """`platform id -> platform-specific id -> debt instrument`"""
  collateral_instruments: dict[str, dict[str, Collateral]]
  """`platform id -> platform-specific id -> collateral instrument`"""
  spam: dict[str, dict[str, SpamAddress]]
  """`platform id -> platform-specific address -> spam address`"""
  pools: dict[str, dict[str, Pool]]
  """`platform id -> platform-specific id -> pool`"""

  @property
  def spam_tokens(self):
    return self.spam

  @property
  def ordered_platforms(self):
    for platform in self.platforms_order:
      yield platform, self.platforms[platform]

  @property
  def blockchains(self):
    return {id: platform for id, platform in self.platforms.items() if platform['kind'] == 'blockchain'}

  @property
  def dexs(self):
    return {id: platform for id, platform in self.platforms.items() if platform['kind'] == 'dex'}

  @staticmethod
  def load(path: Path | str) -> 'Catalogue':
    from . import load
    return load.all(path)
