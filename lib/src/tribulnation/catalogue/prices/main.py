from typing_extensions import Mapping
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from tribulnation.catalogue import Asset
from .sdk import Pricing

@dataclass
class AssetPricing:
  sources: Mapping[str, Pricing]

  @classmethod
  def coingecko_demo_eur(cls):
    from .coingecko import CoingeckoPricing
    coingecko = CoingeckoPricing.new(env='demo', quote='eur')
    return cls(sources={
      'coingecko': coingecko,
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