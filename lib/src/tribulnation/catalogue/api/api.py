from fastapi import FastAPI

from .schema import (
  Stats, Locale,
  AssetSummary, AssetDetail, LocalizedAssetDetail,
  PlatformSummary, PlatformDetail, LocalizedPlatformDetail,
  BlockchainSummary, CexSummary, DexSummary,
)

app = FastAPI()



@app.get('/api/stats.json')
def get_stats() -> Stats:
  """Get global stats about the catalogue"""
  raise NotImplementedError


@app.get('/api/assets.json')
def get_assets() -> list[AssetSummary]:
  """Get a list of all assets with minimal metadata"""
  raise NotImplementedError

@app.get('/api/assets/{id}.json')
def get_asset(id: str) -> AssetDetail:
  """Get detailed metadata for a specific asset"""
  raise NotImplementedError

@app.get('/api/assets/{id}/{locale}.json')
def get_localized_asset(id: str, locale: str) -> LocalizedAssetDetail:
  """Get detailed metadata for a specific asset and locale"""
  raise NotImplementedError


@app.get('/api/platforms.json')
def get_platforms() -> list[PlatformSummary]:
  """Get a list of all platforms with minimal metadata"""
  raise NotImplementedError

@app.get('/api/platforms/{id}.json')
def get_platform(id: str) -> PlatformDetail:
  """Get detailed metadata for a specific platform"""
  raise NotImplementedError

@app.get('/api/platforms/{id}/{locale}.json')
def get_localized_platform(id: str, locale: str) -> LocalizedPlatformDetail:
  """Get detailed metadata for a specific platform and locale"""
  raise NotImplementedError

@app.get('/api/platforms/blockchains.json')
def get_blockchains() -> list[BlockchainSummary]:
  """Get a list of all blockchains with minimal metadata"""
  raise NotImplementedError

@app.get('/api/platforms/cexs.json')
def get_cexs() -> list[CexSummary]:
  """Get a list of all centralized exchanges with minimal metadata"""
  raise NotImplementedError

@app.get('/api/platforms/dexs.json')
def get_dexs() -> list[DexSummary]:
  """Get a list of all decentralized exchanges with minimal metadata"""
  raise NotImplementedError


@app.get('/api/translations/assets/{platform}.json')
def get_asset_translations(platform: str) -> dict[str, str]:
  """Get asset translations for a specific platform"""
  raise NotImplementedError

@app.get('/api/translations/networks/{platform}.json')
def get_network_translations(platform: str) -> dict[str, str]:
  """Get network translations for a specific platform"""
  raise NotImplementedError

