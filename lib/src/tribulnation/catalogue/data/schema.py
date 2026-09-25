from typing_extensions import TypedDict, NotRequired, Literal, Mapping
from decimal import Decimal
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
  delisted: NotRequired[bool]
  """Whether the instrument has been delisted"""
  url: NotRequired[str]
  """Trading page URL for the instrument on the platform"""

class Perpetual(TypedDict):
  exchange: NotRequired[str]
  """Exchange ID (for TradingSDK)"""
  base: str
  """Base asset ID"""
  quote: str
  """Quote asset ID"""
  settlement: str
  """Settlement asset ID"""
  multiplier: NotRequired[Decimal]
  """Contract multiplier for the base asset. E.g. a `10` multiplier means that the index price tracks 10x the base asset price."""
  delisted: NotRequired[bool]
  """Whether the instrument has been delisted"""
  url: NotRequired[str]
  """Trading page URL for the instrument on the platform"""

class Debt(TypedDict):
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

ExternalSource = Literal['coingecko', 'coinmarketcap', 'twelvedata', 'alphavantage', 'fred', 'yahoo']
ExternalIds = Mapping[ExternalSource, str]

class AssetPeg(TypedDict):
  asset: str

AssetCategory = Literal['crypto', 'stock', 'fiat', 'stablecoin', 'commodity', 'fund', 'rwa']

class Asset(TypedDict):
  id: str
  display_name: str
  symbol: str
  category: NotRequired[AssetCategory]
  about: NotRequired[Translations]
  tags: NotRequired[list[str]]
  urls: NotRequired[dict[str, str]]
  icon: NotRequired[str]
  external: NotRequired[ExternalIds]
  pegged_to: NotRequired[AssetPeg]
  replaced_by: NotRequired[str]
  """Asset ID this one was merged into. Ids are never deleted; a merged asset keeps its file as an alias."""

class BasePlatform(TypedDict):
  display_name: str
  about: NotRequired[Translations]
  urls: NotRequired[dict[str, str]]
  icon: NotRequired[str]

class CexPlatform(BasePlatform):
  kind: Literal['cex']

class DexPlatform(BasePlatform):
  kind: Literal['dex']

BlockchainCategory = Literal['antelope', 'cosmos-sdk', 'evm', 'move', 'substrate', 'svm', 'utxo']
BlockchainNamespace = Literal[
  'aleo', 'algorand', 'antelope', 'aptos', 'arweave', 'avax', 'bip122',
  'casper', 'ccd', 'conflux', 'cosmos', 'eip155', 'ergo', 'fil', 'flow',
  'hedera', 'iota', 'klv', 'mina', 'monero', 'mvx', 'neo', 'partisia',
  'polkadot', 'quai', 'solana', 'stacks', 'starknet', 'stellar', 'sui',
  'tezos', 'tron', 'tvm', 'vechain', 'waves', 'xrpl'
]

class Blockchain(BasePlatform):
  kind: Literal['blockchain']
  native_asset: NotRequired[str]
  category: NotRequired[BlockchainCategory]
  chain_id: NotRequired[int | str]
  namespace: NotRequired[BlockchainNamespace]

Platform = CexPlatform | DexPlatform | Blockchain

CorrelationFieldType = Literal['int', 'uint', 'hex', 'string', 'network']
"""Type of a correlation key field, fixing its canonical text form:

- `int` / `uint`: base-10 integer, no leading zeros (`uint` is non-negative)
- `hex`: `0x` followed by lower-case hex digits, leading zeros kept (addresses, hashes)
- `string`: any non-empty text without `:` or whitespace, kept as-is (case-sensitive)
- `network`: a catalogue platform id, e.g. `dydx` or `noble`
"""

class Correlation(TypedDict):
  key: str
  """Key template: the protocol id, then `:`-separated segments, each a `{field}` placeholder or a literal, e.g. `cctp:{source_domain}:{nonce}`"""
  fields: dict[str, CorrelationFieldType]
  """Field name -> type. Exactly the template's placeholders."""

class Protocol(TypedDict):
  """A cross-chain protocol whose correlation keys link both sides of one movement."""
  id: str
  display_name: str
  about: Translations
  urls: dict[str, str]
  correlation: Correlation
  domains: NotRequired[dict[int, str]]
  """Protocol-assigned chain identifier -> catalogue network (platform) id, e.g. CCTP domains"""
