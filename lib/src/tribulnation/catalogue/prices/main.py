from typing_extensions import Mapping, Literal, TYPE_CHECKING
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from tribulnation.catalogue import Asset
from .sdk import Pricing

if TYPE_CHECKING:
  from .coingecko import CoingeckoQuote
  from .coinmarketcap import CoinMarketCapQuote
  from .twelvedata import TwelveDataQuote
  from .alphavantage import AlphaVantageQuote

Quote = Literal['eur', 'usd']

@dataclass
class AssetPricing:
  sources: Mapping[str, Pricing]

  @classmethod
  def new(
    cls, quote: Quote, *, coingecko: bool = False,
    coinmarketcap: bool = False,
    twelvedata: bool = False,
    alphavantage: bool = False,
  ):
    sources: dict[str, Pricing] = {}
    if coingecko:
      from .coingecko import CoingeckoPricing
      sources['coingecko'] = CoingeckoPricing.new(quote=quote)
    if coinmarketcap:
      from .coinmarketcap import CoinMarketCapPricing
      sources['coinmarketcap'] = CoinMarketCapPricing.new(quote=quote)
    if twelvedata:
      from .twelvedata import TwelveDataPricing
      q = 'USD' if quote == 'usd' else 'EUR'
      sources['twelvedata'] = TwelveDataPricing.new(quote=q)
    if alphavantage:
      from .alphavantage import AlphaVantagePricing
      q = 'USD' if quote == 'usd' else 'EUR'
      sources['alphavantage'] = AlphaVantagePricing.new(quote=q)
    return cls(sources=sources)

    
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
    for source, id in asset.get('external', {}).items():
      if sdk := self.sources.get(source):
        if (price := await sdk.current_price(id)) is not None: # type: ignore
          return price

  async def historical_price(self, asset: Asset, time: datetime):
    for source, id in asset.get('external', {}).items():
      if sdk := self.sources.get(source):
        if (price := await sdk.historical_price(id, time)) is not None: # type: ignore
          return price


  async def market_cap(self, asset: Asset) -> Decimal | None:
    for source, id in asset.get('external', {}).items():
      if sdk := self.sources.get(source):
        if (market_cap := await sdk.market_cap(id)) is not None: # type: ignore
          return market_cap