from fastapi import FastAPI

from .schema import (
  Stats, Locale,
  AssetSummary, AssetDetail, LocalizedAssetDetail,
  PlatformSummary, PlatformDetail, LocalizedPlatformDetail,
  BlockchainSummary, CexSummary, DexSummary,
  InstrumentPlatformEntry,
  SpotInstrument, PerpetualInstrument,
  DebtInstrument, PoolInstrument,
  InstrumentReference,
  SpamAddress,
  SymbolsIndex, ExternalIndex, PegsIndex,
)

app = FastAPI(
  title='Tribulnation Catalogue API',
  description='Static JSON API for crypto assets, platforms, translations, instruments, and spam addresses.',
  version='2',
)


@app.get('/api/v1/stats.json')
def get_stats() -> Stats:
  """Global stats about the catalogue."""
  raise NotImplementedError


# Assets

@app.get('/api/v1/assets.json')
def get_assets() -> list[AssetSummary]:
  """List of all assets with minimal metadata."""
  raise NotImplementedError

@app.get('/api/v1/assets/{id}.json')
def get_asset(id: str) -> AssetDetail:
  """Detailed metadata for a specific asset."""
  raise NotImplementedError

@app.get('/api/v1/assets/{id}/{locale}.json')
def get_localized_asset(id: str, locale: Locale) -> LocalizedAssetDetail:
  """Localized metadata for a specific asset."""
  raise NotImplementedError


# Platforms

@app.get('/api/v1/platforms.json')
def get_platforms() -> list[PlatformSummary]:
  """List of all platforms with minimal metadata."""
  raise NotImplementedError

@app.get('/api/v1/platforms/{id}.json')
def get_platform(id: str) -> PlatformDetail:
  """Detailed metadata for a specific platform."""
  raise NotImplementedError

@app.get('/api/v1/platforms/{id}/{locale}.json')
def get_localized_platform(id: str, locale: Locale) -> LocalizedPlatformDetail:
  """Localized metadata for a specific platform."""
  raise NotImplementedError

@app.get('/api/v1/blockchains.json')
def get_blockchains() -> list[BlockchainSummary]:
  """List of all blockchains."""
  raise NotImplementedError

@app.get('/api/v1/cexs.json')
def get_cexs() -> list[CexSummary]:
  """List of all centralized exchanges."""
  raise NotImplementedError

@app.get('/api/v1/dexs.json')
def get_dexs() -> list[DexSummary]:
  """List of all decentralized exchanges."""
  raise NotImplementedError


# Translations

@app.get('/api/v1/translations/assets/{platform}.json')
def get_asset_translations(platform: str) -> dict[str, str]:
  """Maps platform-specific asset IDs to canonical asset IDs."""
  raise NotImplementedError

@app.get('/api/v1/translations/networks/{platform}.json')
def get_network_translations(platform: str) -> dict[str, str]:
  """Maps platform-specific network IDs to canonical platform IDs."""
  raise NotImplementedError


# Instruments

@app.get('/api/v1/instruments/spot.json')
def get_spot_platforms() -> list[InstrumentPlatformEntry]:
  """Platforms with spot pair data."""
  raise NotImplementedError

@app.get('/api/v1/instruments/spot/{platform}.json')
def get_spot_instruments(platform: str) -> dict[str, SpotInstrument]:
  """Spot pairs for a platform, keyed by platform-specific ID."""
  raise NotImplementedError

@app.get('/api/v1/instruments/perpetual.json')
def get_perpetual_platforms() -> list[InstrumentPlatformEntry]:
  """Platforms with perpetual market data."""
  raise NotImplementedError

@app.get('/api/v1/instruments/perpetual/{platform}.json')
def get_perpetual_instruments(platform: str) -> dict[str, PerpetualInstrument]:
  """Perpetual markets for a platform, keyed by platform-specific ID."""
  raise NotImplementedError

@app.get('/api/v1/instruments/debt.json')
def get_debt_platforms() -> list[InstrumentPlatformEntry]:
  """Platforms with debt asset data."""
  raise NotImplementedError

@app.get('/api/v1/instruments/debt/{platform}.json')
def get_debt_instruments(platform: str) -> dict[str, DebtInstrument]:
  """Debt assets for a platform, keyed by address."""
  raise NotImplementedError

@app.get('/api/v1/instruments/pools.json')
def get_pool_platforms() -> list[InstrumentPlatformEntry]:
  """Platforms with liquidity pool data."""
  raise NotImplementedError

@app.get('/api/v1/instruments/pools/{platform}.json')
def get_pool_instruments(platform: str) -> dict[str, PoolInstrument]:
  """Liquidity pools for a platform, keyed by address."""
  raise NotImplementedError

@app.get('/api/v1/instruments/index/{asset}.json')
def get_instrument_index(asset: str) -> list[InstrumentReference]:
  """All instruments where the given asset appears."""
  raise NotImplementedError


# Spam

@app.get('/api/v1/spam/{platform}.json')
def get_spam(platform: str) -> dict[str, SpamAddress]:
  """Spam addresses for a platform, keyed by address."""
  raise NotImplementedError


# Indexes

@app.get('/api/v1/indexes/symbols.json')
def get_symbols_index() -> SymbolsIndex:
  """Maps symbols to possible canonical asset IDs."""
  raise NotImplementedError

@app.get('/api/v1/indexes/external/{provider}.json')
def get_external_index(provider: str) -> ExternalIndex:
  """Maps third-party registry IDs to canonical asset IDs."""
  raise NotImplementedError

@app.get('/api/v1/indexes/pegs.json')
def get_pegs_index() -> PegsIndex:
  """Maps target asset IDs to assets that track or represent them."""
  raise NotImplementedError
