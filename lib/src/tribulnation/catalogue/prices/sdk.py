from typing_extensions import Sequence, Mapping
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
import asyncio

from tribulnation.sdk import SDK

@dataclass
class Price:
  price: Decimal
  time: datetime

class Pricing(SDK):
  @SDK.method

  async def current_price(self, id: str) -> Decimal | None:
    return (await self.current_prices([id])).get(id)

  @SDK.method

  async def current_prices(self, ids: Sequence[str]) -> Mapping[str, Decimal]:
    prices = await asyncio.gather(*(self.current_price(id) for id in ids))
    return {
      id: price
      for id, price in zip(ids, prices)
      if price is not None
    }

  @SDK.method

  async def historical_price(self, id: str, time: datetime) -> Price | None:
    return (await self.historical_prices([id], time)).get(id)

  @SDK.method

  async def historical_prices(self, ids: Sequence[str], time: datetime) -> Mapping[str, Price]:
    prices = await asyncio.gather(*(self.historical_price(id, time) for id in ids))
    return {
      id: price
      for id, price in zip(ids, prices)
      if price is not None
    }


  @SDK.method

  async def market_cap(self, id: str) -> Decimal | None:
    return (await self.market_caps([id])).get(id)


  @SDK.method

  async def market_caps(self, ids: Sequence[str]) -> Mapping[str, Decimal]:
    market_caps = await asyncio.gather(*(self.market_cap(id) for id in ids))
    return {
      id: market_cap
      for id, market_cap in zip(ids, market_caps)
      if market_cap is not None
    }