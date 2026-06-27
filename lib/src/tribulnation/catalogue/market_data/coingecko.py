from typing_extensions import Iterable, TypeVar, Literal, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
import itertools
import functools

import httpx
import coingecko_sdk
from tribulnation.sdk import NetworkError, AuthError, RateLimited, ApiError

from .sdk import Pricing, Price

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
  
  @Pricing.method
  @wrap_exceptions
  async def current_prices(self, ids: Sequence[str]) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for ids_batch in batch(ids, 100):
      r = await self.client.coins.markets.get(vs_currency=self.quote, ids=','.join(ids_batch))
      for coin in r:
        if (p := coin.current_price) is not None:
          out[coin.id] = round_price(Decimal(p))
    return out

  @wrap_exceptions
  async def historical_price(self, id: str, time: datetime) -> Price | None:
    date = round_date(time)
    r = await self.client.coins.history.get(id, date=date.strftime('%Y-%m-%d'))
    if price := (r.market_data.current_price or {}).get(self.quote):
      return Price(price=round_price(Decimal(price)), time=date)

  @wrap_exceptions
  async def market_caps(self, ids: Sequence[str]) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for ids_batch in batch(ids, 100):
      r = await self.client.coins.markets.get(vs_currency=self.quote, ids=','.join(ids_batch))
      for coin in r:
        if (c := coin.market_cap) is not None:
          out[coin.id] = round(Decimal(c), 2)
    return out

