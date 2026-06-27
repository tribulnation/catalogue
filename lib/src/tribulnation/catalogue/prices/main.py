from __future__ import annotations

from typing_extensions import Mapping, TYPE_CHECKING
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from tribulnation.catalogue import Asset
from .sdk import Pricing

if TYPE_CHECKING:
  from .coingecko import CoingeckoQuote
  from .coinmarketcap import CoinMarketCapQuote
  from .twelvedata import TwelveDataQuote

@dataclass
class AssetPricing:
  sources: Mapping[str, Pricing]

  @classmethod
  def coingecko(cls, quote: CoingeckoQuote, *, demo: bool):
    from .coingecko import CoingeckoPricing
    coingecko = CoingeckoPricing.new(env='demo' if demo else 'pro', quote=quote)
    return cls(sources={
      'coingecko': coingecko,
    })
  
  @classmethod
  def coinmarketcap(cls, quote: CoinMarketCapQuote):
    from .coinmarketcap import CoinMarketCapPricing
    coinmarketcap = CoinMarketCapPricing.new(quote=quote)
    return cls(sources={
      'coinmarketcap': coinmarketcap,
    })

  @classmethod
  def twelvedata(cls, quote: TwelveDataQuote = 'USD'):
    from .twelvedata import TwelveDataPricing
    pricing = TwelveDataPricing.new(quote=quote)
    return cls(sources={
      'twelvedata': pricing,
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
