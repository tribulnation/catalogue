from pydantic import BaseModel

class ExternalIds(BaseModel):
  coingecko: str | None = None
  """Coingecko asset ID"""

class AssetPeg(BaseModel):
  asset: str
  """Asset ID"""

class AssetSummary(BaseModel):
  id: str
  """Asset ID"""
  display_name: str
  """Asset display name"""
  symbol: str
  """Asset symbol"""
  icon: str | None = None
  """Asset icon URL"""
  tags: list[str] | None = None
  """Asset tags"""

class BaseAssetDetail(AssetSummary):
  tags: list[str] | None = None
  """Asset tags"""
  urls: dict[str, str] | None = None
  """Asset URLs"""
  icon: str | None = None
  """Asset icon URL"""
  external: ExternalIds | None = None
  """Asset external IDs"""
  pegged_to: AssetPeg | None = None
  """Asset pegged to"""

class AssetDetail(BaseAssetDetail):
  about: dict[str, str] | None = None
  """Asset about"""

class LocalizedAssetDetail(BaseAssetDetail):
  about: str | None = None
  """Asset about"""