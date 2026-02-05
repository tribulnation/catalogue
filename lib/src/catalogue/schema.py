from typing_extensions import TypedDict, NotRequired, Literal, NamedTuple

class Asset(TypedDict):
  display_name: str
  symbol: str
  display_decimals: NotRequired[int]
  about: NotRequired[str]
  tags: NotRequired[list[str]]
  urls: NotRequired[dict[str, str]]
  icon: NotRequired[str]

class Platform(TypedDict):
  display_name: str
  about: NotRequired[str]
  urls: NotRequired[dict[str, str]]
  kind: Literal['cex', 'dex', 'blockchain']
  icon: NotRequired[str]

class Network(TypedDict):
  display_name: str
  about: NotRequired[str]
  urls: NotRequired[dict[str, str]]
  native_asset: NotRequired[str]
  icon: NotRequired[str]

class Catalogue(NamedTuple):
  assets: dict[str, Asset]
  platforms: dict[str, Platform]
  networks: dict[str, Network]
  network_translations: dict[str, dict[str, str]]
  """`platform id -> platform-specific id -> asset id`"""
  asset_translations: dict[str, dict[str, str]]
  """`platform id -> platform-specific id -> asset id`"""