from typing_extensions import TypedDict, NotRequired, Literal, Mapping, Iterable
from dataclasses import dataclass

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

class Collateral(TypedDict):
  asset: str
  """Underlying asset ID"""

class Asset(TypedDict):
  display_name: str
  symbol: str
  display_decimals: NotRequired[int]
  about: NotRequired[Translations]
  tags: NotRequired[list[str]]
  urls: NotRequired[dict[str, str]]
  icon: NotRequired[str]
  coingecko_id: NotRequired[str]

class Platform(TypedDict):
  display_name: str
  about: NotRequired[Translations]
  urls: NotRequired[dict[str, str]]
  kind: Literal['cex', 'dex', 'blockchain']
  icon: NotRequired[str]

class Network(TypedDict):
  display_name: str
  about: NotRequired[Translations]
  urls: NotRequired[dict[str, str]]
  native_asset: NotRequired[str]
  icon: NotRequired[str]

@dataclass
class Catalogue:
  assets: dict[str, Asset]
  assets_order: list[str]
  platforms: dict[str, Platform]
  platforms_order: list[str]
  networks: dict[str, Network]
  networks_order: list[str]
  network_translations: dict[str, dict[str, str]]
  """`platform id -> platform-specific id -> asset id`"""
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

  @property
  def ordered_assets(self):
    for asset in self.assets_order:
      yield asset, self.assets[asset]

  @property
  def ordered_platforms(self):
    for platform in self.platforms_order:
      yield platform, self.platforms[platform]

  @property
  def ordered_networks(self):
    for network in self.networks_order:
      yield network, self.networks[network]

  @staticmethod
  def load(path: str) -> 'Catalogue':
    from . import load
    return load.all(path)
