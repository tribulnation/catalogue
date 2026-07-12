from typing_extensions import Any, Mapping, Literal
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import asyncio

from tribulnation.sdk import Context, Error
from tribulnation.catalogue import Asset
from .sdk import Pricing, Price, Stats, Quote, Source

@dataclass
class MarketData:
  Context = Context
  Quote = Quote
  Source = Source
  
  sources: Mapping[Source, Pricing]
  ctx: Context = field(default_factory=Context)

  @classmethod
  def new(
    cls, *sources: Source,
    quote: Quote = 'usd',
    ctx: Context | None = None,
  ):
    """Construct a new `MarketData` instance with multiple sources."""
    if not sources:
      raise ValueError('Must specify at least one source')

    sdks: dict[Source, Pricing] = {source: Pricing.of(source, quote=quote) for source in sources}
    return cls(sources=sdks, ctx=ctx or Context())


  async def historical_price(self, asset: Asset, time: datetime) -> tuple[Price|None, Mapping[Source, Error]]:
    """Fetch the historical price of an asset at a specific time from the first available source.
    
    Returns:
      (price, errors):
        - `price`: the historical price of the asset at the specified time (or `None` if not found), and
        - `errors`: a mapping of sources to any errors encountered while fetching the price.
    """
    errors: dict[Source, Error] = {}
    with self.ctx.use():
      if (sdk := self.sources.get('catalogue-pro')) is not None:
        try:
          if (price := await sdk.historical_price(asset['id'], time)) is not None:
            return price, errors
        except Error as e:
          errors['catalogue-pro'] = e
      for source, id in asset.get('external', {}).items():
        if sdk := self.sources.get(source):
          try:
            if (price := await sdk.historical_price(id, time)) is not None:
              return price, errors
          except Error as e:
            errors[source] = e
      
    return None, errors

  async def current_price(self, asset: Asset) -> tuple[Decimal|None, Mapping[Source, Error]]:
    """Fetch the current price of an asset from the first available source.
    
    Returns:
      (price, errors):
        - `price`: the current price of the asset (or `None` if not found), and
        - `errors`: a mapping of sources to any errors encountered while fetching the price.
    """
    id = asset['id']
    stats, errors = await self.current_stats({id: asset})
    if (s := stats.get(id)) is not None:
      return s.price, errors
    else:
      return None, errors

  async def current_stats(self, assets: Mapping[str, Asset]) -> tuple[Mapping[str, Stats], Mapping[Source, Error]]:
    """Fetch the current stats of multiple assets from all available sources.

    Returns:
      (stats, errors):
        - `stats`: a mapping of asset IDs to their current stats, and
        - `errors`: a mapping of sources to any errors encountered while fetching the prices.
    """
    async def source_stats(src: MarketData.Source, map: dict[str, str]) -> tuple[dict[str, Stats], Mapping[Source, Error]]:
      sdk = self.sources[src]
      try:
        stats = await sdk.current_stats(list(map))
        result = {map[ext_id]: s for ext_id, s in stats.items()}
        return result, {}
      except Error as e:
        return {}, {src: e}

    remaining = dict(assets)
    all_stats: dict[str, Stats] = {}
    all_errors: dict[Source, Error] = {}
    failed_sources: set[Source] = set()

    if (sdk := self.sources.get('catalogue-pro')) is not None:
      try:
        stats = await sdk.current_stats(assets)
        all_stats.update(stats)
        for asset_id in stats:
          remaining.pop(asset_id, None)
      except Error as e:
        all_errors['catalogue-pro'] = e
        failed_sources.add('catalogue-pro')

    while remaining:
      available: dict[Source, Pricing] = {src: sdk for src, sdk in self.sources.items() if src not in failed_sources}
      source_maps = classify_sources(remaining, available)
      if not any(source_maps.values()):
        break

      with self.ctx.use():
        results = await asyncio.gather(*[
          source_stats(src, map)
          for src, map in source_maps.items() if map
        ])

      had_failure = False
      for (src, map), (result, error) in zip(
        ((s, m) for s, m in source_maps.items() if m), results
      ):
        all_stats.update(result)
        if error:
          all_errors.update(error)
          failed_sources.add(src) # type: ignore
          had_failure = True
        else:
          for asset_id in map.values():
            remaining.pop(asset_id, None)

      if not had_failure:
        break

    for id, asset in assets.items():
      if id not in all_stats:
        if (peg := asset.get('pegged_to')) and (peg_stats := all_stats.get(peg['asset'])):
          all_stats[id] = Stats(price=peg_stats.price)

    return all_stats, all_errors
    

def classify_sources(assets: Mapping[str, Asset], sources: Mapping[Source, Any]) -> dict[Source, dict[str, str]]:
  external: dict[Source, dict[str, str]] = {
    src: {}
    for src in sources
  }

  for id, asset in assets.items():
    for src, external_id in asset.get('external', {}).items():
      if src in external:
        external[src][external_id] = id
        break
  
  return external