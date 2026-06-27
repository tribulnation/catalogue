from typing_extensions import TypedDict, NotRequired, Literal
from datetime import datetime

Locale = Literal['ca', 'es', 'en']
Translations = dict[Locale, str]

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
  coinmarketcap: str
  twelvedata: str
  alphavantage: str

class AssetPeg(TypedDict):
  asset: str

class Asset(TypedDict):
  display_name: str
  symbol: str
  about: NotRequired[Translations]
  tags: NotRequired[list[str]]
  urls: NotRequired[dict[str, str]]
  icon: NotRequired[str]
  external: NotRequired[ExternalIds]
  pegged_to: NotRequired[AssetPeg]

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

