from typing_extensions import Literal
from pydantic import BaseModel

PlatformKind = Literal['blockchain', 'cex', 'dex']

class PlatformSummary(BaseModel):
  id: str
  """Platform ID"""
  display_name: str
  """Platform display name"""
  kind: PlatformKind
  """Platform kind"""
  icon: str | None = None
  """Platform icon URL"""
  
class BlockchainSummary(PlatformSummary):
  kind: Literal['blockchain'] # type: ignore
  """Platform kind"""
  native_asset: str | None = None
  """Platform native asset"""
  category: str | None = None
  """Platform category"""
  namespace: str | None = None
  """Platform namespace"""
  chain_id: int | str | None = None
  """Platform chain ID"""

class CexSummary(PlatformSummary):
  kind: Literal['cex'] # type: ignore
  """Platform kind"""

class DexSummary(PlatformSummary):
  kind: Literal['dex'] # type: ignore
  """Platform kind"""

class BasePlatformDetail(PlatformSummary):
  urls: dict[str, str] | None = None
  """Platform URLs"""
  icon: str | None = None
  """Platform icon URL"""

class PlatformDetail(BasePlatformDetail):
  about: dict[str, str] | None = None
  """Platform about"""
  native_asset: str | None = None
  """Native asset ID (blockchains only)"""
  category: str | None = None
  """Category (blockchains only, e.g. 'evm')"""
  namespace: str | None = None
  """CAIP-2 namespace (blockchains only)"""
  chain_id: int | str | None = None
  """Chain ID (blockchains only)"""

class LocalizedPlatformDetail(BasePlatformDetail):
  about: str | None = None
  """Platform about"""