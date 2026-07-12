from typing_extensions import Collection, Mapping, Literal
from dataclasses import dataclass
from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import datetime

from tribulnation.sdk import SDK
from tribulnation.catalogue import ExternalSource

Source = ExternalSource | Literal['catalogue-pro']
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
  def of(source: Source, *, quote: Quote = 'usd') -> 'Pricing':
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
    elif source == 'fred':
      from .fred import FredPricing
      q = 'USD' if quote == 'usd' else 'EUR'
      return FredPricing.new(quote=q)
    elif source == 'catalogue-pro':
      from .catalogue_pro import CatalogueProPricing
      return CatalogueProPricing.new()
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
