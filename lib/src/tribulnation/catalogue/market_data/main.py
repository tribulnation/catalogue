from typing_extensions import Mapping, Literal, TYPE_CHECKING, TypeVar, TypedDict, Unpack
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from tribulnation.sdk import SDK
from tribulnation.catalogue import Asset
from .sdk import Pricing
import logging

default_logger = logging.getLogger(__name__)

S = TypeVar('S', bound=SDK)

class RetryConfig(TypedDict, total=False):
  max_retries: int | None
  base_delay: float
  max_delay: float | None

def retried(sdk: S, **kwargs: Unpack[RetryConfig]) -> S:
  from tribulnation.sdk.core import instrument, exponential_retry, NetworkError, RateLimited
  return instrument(sdk, exponential_retry(NetworkError, RateLimited, **kwargs))

if TYPE_CHECKING:
  from .coingecko import CoingeckoQuote
  from .coinmarketcap import CoinMarketCapQuote
  from .twelvedata import TwelveDataQuote
  from .alphavantage import AlphaVantageQuote

Quote = Literal['eur', 'usd']
Source = Literal['coingecko', 'coinmarketcap', 'twelvedata', 'alphavantage']

@dataclass
class MarketData:
  sources: Mapping[str, Pricing]
  logger: logging.Logger | None = default_logger

  @classmethod
  def new(
    cls, quote: Quote, *sources: Source,
    logger: logging.Logger | None = default_logger,
    **retry: Unpack[RetryConfig],
  ):
    if not sources:
      raise ValueError('Must specify at least one source')

    built: dict[str, Pricing] = {}
    for source in sources:
      if source == 'coingecko':
        from .coingecko import CoingeckoPricing
        built['coingecko'] = CoingeckoPricing.new(quote=quote)
      elif source == 'coinmarketcap':
        from .coinmarketcap import CoinMarketCapPricing
        built['coinmarketcap'] = CoinMarketCapPricing.new(quote=quote)
      elif source == 'twelvedata':
        from .twelvedata import TwelveDataPricing
        q = 'USD' if quote == 'usd' else 'EUR'
        built['twelvedata'] = TwelveDataPricing.new(quote=q)
      elif source == 'alphavantage':
        from .alphavantage import AlphaVantagePricing
        q = 'USD' if quote == 'usd' else 'EUR'
        built['alphavantage'] = AlphaVantagePricing.new(quote=q)
      else:
        raise ValueError(f'Unknown source: {source!r}')

    built = {k: retried(v, **retry) for k, v in built.items()}
    return cls(sources=built, logger=logger)


  @classmethod
  def coingecko(cls, quote: 'CoingeckoQuote', *, demo: bool):
    from .coingecko import CoingeckoPricing
    coingecko = CoingeckoPricing.new(env='demo' if demo else 'pro', quote=quote)
    return cls(sources={
      'coingecko': coingecko,
    })
  
  @classmethod
  def coinmarketcap(cls, quote: 'CoinMarketCapQuote'):
    from .coinmarketcap import CoinMarketCapPricing
    coinmarketcap = CoinMarketCapPricing.new(quote=quote)
    return cls(sources={
      'coinmarketcap': coinmarketcap,
    })

  @classmethod
  def twelvedata(cls, quote: 'TwelveDataQuote' = 'USD'):
    from .twelvedata import TwelveDataPricing
    pricing = TwelveDataPricing.new(quote=quote)
    return cls(sources={
      'twelvedata': pricing,
    })

  @classmethod
  def alphavantage(cls, quote: 'AlphaVantageQuote' = 'USD'):
    from .alphavantage import AlphaVantagePricing
    pricing = AlphaVantagePricing.new(quote=quote)
    return cls(sources={
      'alphavantage': pricing,
    })

  async def current_price(self, asset: Asset) -> Decimal | None:
    exc: Exception | None = None
    for source, id in asset.get('external', {}).items():
      if sdk := self.sources.get(source):
        try:
          if (price := await sdk.current_price(id)) is not None: # type: ignore
            return price
        except Exception as e:
          if self.logger is not None:
            self.logger.error(f"Error fetching price from {source}: {e}")
          exc = e
    if exc is not None:
      raise exc


  async def historical_price(self, asset: Asset, time: datetime):
    exc: Exception | None = None
    for source, id in asset.get('external', {}).items():
      if sdk := self.sources.get(source):
        try:
          if (price := await sdk.historical_price(id, time)) is not None: # type: ignore
            return price
        except Exception as e:
          if self.logger is not None:
            self.logger.error(f"Error fetching historical price from {source}: {e}")
          exc = e
    if exc is not None:
      raise exc


  async def market_cap(self, asset: Asset) -> Decimal | None:
    exc: Exception | None = None
    for source, id in asset.get('external', {}).items():
      if sdk := self.sources.get(source):
        try:
          if (market_cap := await sdk.market_cap(id)) is not None: # type: ignore
            return market_cap
        except Exception as e:
          if self.logger is not None:
            self.logger.error(f"Error fetching market cap from {source}: {e}")
          exc = e
    if exc is not None:
      raise exc