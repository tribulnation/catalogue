from typing_extensions import TypedDict, NotRequired, Literal, NamedTuple, Mapping

Locale = Literal['ca', 'es', 'en']
Translations = Mapping[Locale, str]

class Spot(TypedDict):
  id: str
  """Platform-specific ID"""
  base: str
  """Base asset ID"""
  quote: str
  """Quote asset ID"""

class Perpetual(TypedDict):
  id: str
  """Platform-specific ID"""
  base: str
  """Base asset ID"""
  quote: str
  """Quote asset ID"""
  settlement: str
  """Settlement asset ID"""

class Asset(TypedDict):
  display_name: str
  symbol: str
  display_decimals: NotRequired[int]
  about: NotRequired[Translations]
  tags: NotRequired[list[str]]
  urls: NotRequired[dict[str, str]]
  icon: NotRequired[str]
  rank: int
  coingecko_id: NotRequired[str]

class Platform(TypedDict):
  display_name: str
  about: NotRequired[Translations]
  urls: NotRequired[dict[str, str]]
  kind: Literal['cex', 'dex', 'blockchain']
  icon: NotRequired[str]
  rank: int

class Network(TypedDict):
  display_name: str
  about: NotRequired[Translations]
  urls: NotRequired[dict[str, str]]
  native_asset: NotRequired[str]
  icon: NotRequired[str]
  rank: int

class Catalogue(NamedTuple):
  assets: dict[str, Asset]
  platforms: dict[str, Platform]
  networks: dict[str, Network]
  network_translations: dict[str, dict[str, str]]
  """`platform id -> platform-specific id -> asset id`"""
  asset_translations: dict[str, dict[str, str]]
  """`platform id -> platform-specific id -> asset id`"""
  spot_instruments: dict[str, dict[str, Spot]]
  """`platform id -> platform-specific id -> spot instrument`"""
  perpetual_instruments: dict[str, dict[str, Perpetual]]
  """`platform id -> platform-specific id -> perpetual instrument`"""