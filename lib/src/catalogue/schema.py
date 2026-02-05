from typing_extensions import TypedDict, NotRequired, Literal, NamedTuple

class Asset(TypedDict):
  display_name: str
  symbol: str
  display_decimals: NotRequired[int]
  tags: NotRequired[list[str]]
  urls: NotRequired[dict[str, str]]
  icon: NotRequired[str]

class Platform(TypedDict):
  display_name: str
  urls: NotRequired[dict[str, str]]
  kind: Literal['cex', 'dex', 'blockchain']
  icon: NotRequired[str]

class Network(TypedDict):
  display_name: str
  urls: NotRequired[dict[str, str]]
  native_asset: NotRequired[str]
  icon: NotRequired[str]

class AssetTranslation(TypedDict):
  asset: str
  id: str
  """Platform-specific identifier."""

class NetworkTranslation(TypedDict):
  network: str
  id: str
  """Platform-specific identifier."""

class Catalogue(NamedTuple):
  assets: dict[str, Asset]
  platforms: dict[str, Platform]
  networks: dict[str, Network]
  network_translations: dict[str, list[NetworkTranslation]]
  asset_translations: dict[str, list[AssetTranslation]]