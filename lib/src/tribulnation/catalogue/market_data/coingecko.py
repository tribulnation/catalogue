from typing_extensions import Iterable, TypeVar, Literal, Collection
from dataclasses import dataclass
from datetime import datetime, timedelta

from decimal import Decimal
import itertools
import functools

import httpx
import coingecko_sdk
from tribulnation.sdk import NetworkError, AuthError, RateLimited, ApiError

from .sdk import Pricing, Price, Stats

T = TypeVar('T')

def batch(iterable: Iterable[T], size: int) -> Iterable[list[T]]:
  it = iter(iterable)
  batch = list(itertools.islice(it, size))
  while batch:
    yield batch
    batch = list(itertools.islice(it, size))

def round_price(price: Decimal):
  if price >= 0.1:
    return round(price, 2)
  else:
    _, digits, exp = price.as_tuple()
    if not isinstance(exp, int):
      raise ValueError(f'{price} has non-integer exponent')
    first_digit_exp = abs(exp) - len(digits) + 1
    digits = first_digit_exp + 2
    return round(price, digits)

def round_date(date: datetime):
  if date.hour > 12:
    date = date + timedelta(days=1)
  return date


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
    client = coingecko_sdk.AsyncCoingecko() if env is None else coingecko_sdk.AsyncCoingecko(environment=env)
    return cls(client=client, quote=quote)
  
  @wrap_exceptions
  async def currency_price(self, currency: str, *, reference_asset: str = 'bitcoin') -> Decimal | None:
    """Deduce the price of a currency by comparing price of a given reference asset in both the currency and USD"""
    usd = (await self.client.coins.markets.get(vs_currency='usd', ids=reference_asset))[0].current_price
    other = (await self.client.coins.markets.get(vs_currency=currency, ids=reference_asset))[0].current_price
    if usd and other:
      return  round_price(Decimal(usd) / Decimal(other))
      
    
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


  @wrap_exceptions
  async def current_stats(self, ids: Collection[str]) -> dict[str, Stats]:
    out: dict[str, Stats] = {}
    currency_ids = {id for id in ids if id.startswith('currency:')}
    normal_ids = [id for id in ids if id not in currency_ids]

    for ids_batch in batch(normal_ids, 100):
      r = await self.client.coins.markets.get(vs_currency=self.quote, ids=','.join(ids_batch))
      for coin in r:
        s = out.setdefault(coin.id, Stats())
        if (p := coin.current_price) is not None:
          s.price = round_price(Decimal(p))
        if (c := coin.market_cap) is not None:
          s.market_cap = round(Decimal(c), 2)

    for currency in currency_ids:
      if price := await self.currency_price(currency.removeprefix('currency:')):
        out[currency] = Stats(price=price)

    return out
  

  @wrap_exceptions
  async def historical_price(self, id: str, time: datetime) -> Price | None:
    if id.startswith('currency:'):
      return await self.currency_historical_price(id.removeprefix('currency:'), time)
    else:
      date = round_date(time)
      r = await self.client.coins.history.get(id, date=date.strftime('%Y-%m-%d'))
      if price := (r.market_data.current_price or {}).get(self.quote):
        return Price(price=round_price(Decimal(price)), time=date)


