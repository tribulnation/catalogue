from typing_extensions import Literal, Collection
from dataclasses import dataclass
from datetime import datetime

from decimal import Decimal
import functools
import os

import httpx
import coingecko_sdk
from tribulnation.sdk import SDK, NetworkError, AuthError, RateLimited, ApiError

from .sdk import Pricing, Price, Stats
from .util import round_price, round_date, batch


def wrap_exceptions(f):
  @functools.wraps(f)
  async def wrapper(*args, **kwargs):
    try:
      return await f(*args, **kwargs)
    except httpx.ConnectError as e:
      raise NetworkError(*e.args) from e
    except coingecko_sdk.AuthenticationError as e:
      raise AuthError(*e.args) from e
    except coingecko_sdk.RateLimitError as e:
      raise RateLimited(*e.args) from e
    except coingecko_sdk.APIError as e:
      raise ApiError(*e.args) from e
  return wrapper

CoingeckoQuote = Literal['eur', 'usd']

@dataclass
class CoingeckoPricing(Pricing):
  client: coingecko_sdk.AsyncCoingecko
  quote: CoingeckoQuote

  @classmethod
  def new(cls, *, env: Literal['demo', 'pro'] | None = None, quote: CoingeckoQuote = 'eur'):
    if env is None:
      if os.environ.get('COINGECKO_PRO_API_KEY'):
        env = 'pro'
      elif os.environ.get('COINGECKO_DEMO_API_KEY'):
        env = 'demo'
    client = coingecko_sdk.AsyncCoingecko() if env is None else coingecko_sdk.AsyncCoingecko(environment=env)
    return cls(client=client, quote=quote)
  
  @SDK.method
  @wrap_exceptions
  async def currency_price(self, currency: str, *, reference_asset: str = 'bitcoin') -> Decimal | None:
    """Deduce the price of a currency by comparing price of a given reference asset in both the currency and USD"""
    usd = (await self.client.coins.markets.get(vs_currency='usd', ids=reference_asset))[0].current_price
    other = (await self.client.coins.markets.get(vs_currency=currency, ids=reference_asset))[0].current_price
    if usd and other:
      return  round_price(Decimal(usd) / Decimal(other))
      
    
  @SDK.method
  @wrap_exceptions
  async def currency_historical_price(self, currency: str, time: datetime, *, reference_asset: str = 'bitcoin') -> Price | None:
    """Deduce the historical price of a currency by comparing price of a given reference asset in both the currency and USD"""
    date = round_date(time)
    r = await self.client.coins.history.get(reference_asset, date=date.strftime('%Y-%m-%d'))
    if price := r.market_data.current_price:
      usd = price.get('usd')
      other = price.get(currency)
      if usd and other:
        price = round_price(Decimal(other) / Decimal(usd))
        return Price(price=price, time=date)


  @SDK.method
  @wrap_exceptions
  async def _fetch_markets(self, ids: list[str]) -> dict[str, Stats]:
    """Fetch market data for a batch of coin IDs."""
    out: dict[str, Stats] = {}
    r = await self.client.coins.markets.get(vs_currency=self.quote, ids=','.join(ids))
    for coin in r:
      s = out.setdefault(coin.id, Stats())
      if (p := coin.current_price) is not None:
        s.price = round_price(Decimal(p))
      if (c := coin.market_cap) is not None:
        s.market_cap = round(Decimal(c), 2)
    return out

  async def current_stats(self, ids: Collection[str]) -> dict[str, Stats]:
    """Fetch current stats, batching normal IDs and resolving currencies."""
    out: dict[str, Stats] = {}
    currency_ids = {id for id in ids if id.startswith('currency:')}
    normal_ids = [id for id in ids if id not in currency_ids]
    for ids_batch in batch(normal_ids, 100):
      out.update(await self._fetch_markets(ids_batch))
    for currency in currency_ids:
      if price := await self.currency_price(currency.removeprefix('currency:')):
        out[currency] = Stats(price=price)
    return out

  @SDK.method
  @wrap_exceptions
  async def _fetch_coin_history(self, id: str, time: datetime) -> Price | None:
    """Fetch historical price for a single coin."""
    date = round_date(time)
    r = await self.client.coins.history.get(id, date=date.strftime('%Y-%m-%d'))
    if price := (r.market_data.current_price or {}).get(self.quote):
      return Price(price=round_price(Decimal(price)), time=date)

  async def historical_price(self, id: str, time: datetime) -> Price | None:
    """Fetch historical price, dispatching currencies vs coins."""
    if id.startswith('currency:'):
      return await self.currency_historical_price(id.removeprefix('currency:'), time)
    return await self._fetch_coin_history(id, time)


