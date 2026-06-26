from datetime import datetime
from pydantic import BaseModel


class SpamAddress(BaseModel):
  reason: str | None = None
  """Reason the address was flagged"""
  source: str | None = None
  """Source that reported the address"""
  reported_at: datetime | None = None
  """When the address was reported"""
