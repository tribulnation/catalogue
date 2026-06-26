from pydantic import BaseModel

class Stats(BaseModel):
  assets: int
  """Number of assets in the catalogue"""
  platforms: int
  """Number of platforms in the catalogue"""
  blockchains: int
  """Number of blockchains in the catalogue"""
  cexs: int
  """Number of centralized exchanges in the catalogue"""
  dexs: int
  """Number of decentralized exchanges in the catalogue"""
  asset_translations: int
  """Number of asset translations in the catalogue"""
  network_translations: int
  """Number of network translations in the catalogue"""
  assets_with_icons: int
  """Number of assets with icons in the catalogue"""
  assets_with_external_ids: int
  """Number of assets with external IDs in the catalogue"""
  assets_with_pegs: int
  """Number of assets with pegs in the catalogue"""
  spot_instruments: int
  """Number of spot instruments in the catalogue"""
  perpetual_instruments: int
  """Number of perpetual instruments in the catalogue"""
  spam_addresses: int
  """Number of spam addresses in the catalogue"""