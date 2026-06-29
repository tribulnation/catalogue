from typing import Literal
from pydantic import BaseModel

InstrumentKind = Literal['spot', 'perpetual', 'debt', 'pool']
InstrumentRole = Literal['base', 'quote', 'settlement', 'asset']


class InstrumentPlatformEntry(BaseModel):
  platform: str
  """Platform ID"""
  count: int
  """Number of instruments on this platform"""


class SpotInstrument(BaseModel):
  id: str
  """Platform-specific instrument ID"""
  base: str
  """Base asset ID"""
  quote: str
  """Quote asset ID"""
  exchange: str | None = None
  """Exchange sub-account identifier"""


class PerpetualInstrument(BaseModel):
  id: str
  """Platform-specific instrument ID"""
  base: str
  """Base asset ID"""
  quote: str
  """Quote asset ID"""
  settlement: str
  """Settlement asset ID"""
  exchange: str | None = None
  """Exchange sub-account identifier"""


class DebtInstrument(BaseModel):
  id: str
  """Platform-specific token address"""
  asset: str
  """Underlying asset ID"""
  name: str
  """Token name"""


class PoolInstrument(BaseModel):
  id: str
  """Platform-specific pool address"""
  assets: list[str]
  """Asset IDs in the pool"""
  name: str
  """Pool name"""


class InstrumentReference(BaseModel):
  kind: InstrumentKind
  """Instrument type"""
  platform: str
  """Platform ID"""
  id: str
  """Platform-specific instrument ID"""
  role: InstrumentRole
  """Role of the asset in this instrument"""
