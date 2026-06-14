from typing_extensions import TypedDict, NotRequired, Literal, Mapping, Iterable
from dataclasses import dataclass
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

class SpamToken(TypedDict):
  ...

class Asset(TypedDict):
  display_name: str
  symbol: str
  display_decimals: NotRequired[int]
  about: NotRequired[Translations]
  tags: NotRequired[list[str]]
  urls: NotRequired[dict[str, str]]
  icon: NotRequired[str]
  coingecko_id: NotRequired[str]

class BasePlatform(TypedDict):
  display_name: str
  about: NotRequired[Translations]
  urls: NotRequired[dict[str, str]]
  icon: NotRequired[str]

class CexPlatform(BasePlatform):
  kind: Literal['cex']

class DexPlatform(BasePlatform):
  kind: Literal['dex']

class Blockchain(BasePlatform):
  kind: Literal['blockchain']
  native_asset: NotRequired[str]

Platform = CexPlatform | DexPlatform | Blockchain

@dataclass
class Catalogue:
  assets: dict[str, Asset]
  assets_order: list[str]
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
  spam_tokens: dict[str, dict[str, SpamToken]]
  """`platform id -> platform-specific id -> spam token`"""
  pools: dict[str, dict[str, Pool]]
  """`platform id -> platform-specific id -> pool`"""

  @property
  def ordered_assets(self):
    for asset in self.assets_order:
      yield asset, self.assets[asset]

  @property
  def ordered_platforms(self):
    for platform in self.platforms_order:
      yield platform, self.platforms[platform]

  @staticmethod
  def load(path: Path | str) -> 'Catalogue':
    from . import load
    return load.all(path)
