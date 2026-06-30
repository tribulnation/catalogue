from typing_extensions import Collection, Mapping, Literal, overload
from dataclasses import dataclass
from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import datetime
import asyncio

from tribulnation.sdk import SDK
from tribulnation.catalogue import ExternalSource

Quote = Literal['eur', 'usd']

@dataclass
class Price:
  price: Decimal
  time: datetime

@dataclass(kw_only=True)
class Stats:
  price: Decimal | None = None
  market_cap: Decimal | None = None

class Pricing(SDK, ABC):
  @staticmethod
  def of(source: ExternalSource, *, quote: Quote = 'usd') -> 'Pricing':
    """"""
    if source == 'coingecko':
      from .coingecko import CoingeckoPricing
      return CoingeckoPricing.new(quote=quote)
    elif source == 'coinmarketcap':
      from .coinmarketcap import CoinMarketCapPricing
      return CoinMarketCapPricing.new(quote=quote)
    elif source == 'twelvedata':
      from .twelvedata import TwelveDataPricing
      q = 'USD' if quote == 'usd' else 'EUR'
      return TwelveDataPricing.new(quote=q)
    elif source == 'alphavantage':
      from .alphavantage import AlphaVantagePricing
      q = 'USD' if quote == 'usd' else 'EUR'
      return AlphaVantagePricing.new(quote=q)
    else:
      raise ValueError(f'Unknown source: {source!r}')

  @SDK.method
  @abstractmethod
  async def current_stats(self, ids: Collection[str]) -> Mapping[str, Stats]:
    """Fetch the current price and market cap of an asset by its external ID."""
    
  @SDK.method
  @abstractmethod
  async def historical_price(self, id: str, time: datetime) -> Price | None:
    """Fetch the historical price of an asset by its external ID at a specific time."""

  async def current_price(self, id: str) -> Decimal | None:
    """Fetch the current price of an asset by its external ID."""
    if (stats := await self.current_stats([id])).get(id) is not None:
      return stats[id].price
    
  async def market_cap(self, id: str) -> Decimal | None:
    """Fetch the current market cap of an asset by its external ID."""
    if (stats := await self.current_stats([id])).get(id) is not None:
      return stats[id].market_cap
