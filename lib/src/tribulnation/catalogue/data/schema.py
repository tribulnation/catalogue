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

class DepositFields(TypedDict):
  """Names of the fields of one operation in a deposit lookup's response."""
  deposit_address: str
  """The address the protocol assigned, to which the sender sends to start the operation"""
  sender: str
  """The sending address on the source chain"""
  source_chain: str
  """The source chain, a key of the protocol's `chains`"""
  destination_chain: str
  """The destination chain, a key of the protocol's `chains`"""
  destination_address: str
  """The receiving address on the destination chain"""
  asset: str
  """The asset, a key of the protocol's `assets`"""
  time: NotRequired[str]
  """When the protocol created the operation: ISO 8601 or integer milliseconds"""

class DepositLookup(TypedDict):
  """A public HTTP API listing an address's operations, each naming its protocol-assigned deposit address.

  For protocols that assign a deposit address per user (e.g. Hyperunit), so no fixed address
  list can be published. A unit may capture the response as evidence for recognising a send
  to a deposit address; it never supplies a correlation key field.
  """
  url: str
  """`GET` URL template with one `{address}` placeholder: the sender's address"""
  operations: str
  """Top-level response field holding the list of operations"""
  fields: DepositFields

class Protocol(TypedDict):
  """A cross-chain protocol: its correlation keys and the data that recognises its movements."""
  id: str
  display_name: str
  about: Translations
  urls: dict[str, str]
  correlation: NotRequired[Correlation]
  """Absent when no key can be derived by both sides (e.g. a payout that carries no operation data)"""
  domains: NotRequired[dict[int, str]]
  """Protocol-assigned chain identifier -> catalogue network (platform) id, e.g. CCTP domains"""
  chains: NotRequired[dict[str, str]]
  """Protocol-assigned chain name -> catalogue network (platform) id, e.g. Hyperunit's `hyperliquid`"""
  channels: NotRequired[dict[str, dict[str, str]]]
  """Catalogue network id -> its channel identifier -> the catalogue network at the other end, e.g. IBC's `dydx` `channel-0` -> `noble`"""
  assets: NotRequired[dict[str, str]]
  """Protocol-assigned asset name -> catalogue asset id, e.g. Hyperunit's `eth`"""
  deposits: NotRequired[DepositLookup]
