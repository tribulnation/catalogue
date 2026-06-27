from typing_extensions import Literal, Sequence, Mapping, Any
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import functools
import os

import httpx
from pydantic import ValidationError
from tribulnation.sdk import NetworkError, AuthError, RateLimited, ApiError
from typed_core import HttpClient

from .coingecko import round_price
from .sdk import Pricing, Price


BASE_URL = 'https://www.alphavantage.co/query'

# Supported commodity function names
COMMODITY_FUNCTIONS = {
  'WTI', 'BRENT', 'NATURAL_GAS', 'COPPER', 'ALUMINUM',
  'WHEAT', 'CORN', 'COTTON', 'SUGAR', 'COFFEE',
}

AlphaVantageQuote = Literal['USD', 'EUR']


def _is_forex(id: str) -> bool:
  return '/' in id


def _check_body_error(data: Any) -> None:
  if 'Error Message' in data:
    raise ApiError(str(data['Error Message']))
  if 'Note' in data:
    raise RateLimited(str(data['Note']))
  if 'Information' in data:
    raise RateLimited(str(data['Information']))


def _error_message(response: httpx.Response) -> str:
  try:
    payload = response.json()
  except ValueError:
    return response.text
  if isinstance(payload, Mapping) and payload.get('Error Message'):
    return str(payload['Error Message'])
  return response.text


def wrap_exceptions(f):
  @functools.wraps(f)
  async def wrapper(*args, **kwargs):
    try:
      return await f(*args, **kwargs)
    except httpx.ConnectError as e:
      raise NetworkError(*e.args) from e
    except httpx.TimeoutException as e:
      raise NetworkError(*e.args) from e
    except httpx.HTTPStatusError as e:
      status = e.response.status_code
      message = _error_message(e.response)
      if status == 401:
        raise AuthError(message) from e
      if status == 429:
        raise RateLimited(message) from e
      raise ApiError(message) from e
    except ValidationError as e:
      raise ApiError(*e.args) from e
  return wrapper


@dataclass
class AlphaVantagePricing(Pricing):
  quote: AlphaVantageQuote
  params: dict[str, str] = field(kw_only=True, repr=False)
  client: HttpClient = field(kw_only=True, default_factory=HttpClient)

  async def __aenter__(self):
    await self.client.__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.client.__aexit__(exc_type, exc_value, traceback)

  @classmethod
  def new(cls, *, api_key: str | None = None, quote: AlphaVantageQuote = 'USD'):
    api_key = api_key or os.environ.get('ALPHAVANTAGE_API_KEY')
    params: dict[str, str] = {}
    if api_key:
      params['apikey'] = api_key
    return cls(quote=quote, params=params)

  @wrap_exceptions
  async def current_prices(self, ids: Sequence[str]) -> dict[str, Decimal]:
    # Alpha Vantage has no batch endpoint — fetch sequentially
    out: dict[str, Decimal] = {}
    for id in ids:
      price = await self._fetch_current(id)
      if price is not None:
        out[id] = price
    return out

  async def _fetch_current(self, id: str) -> Decimal | None:
    if _is_forex(id):
      from_sym, to_sym = id.split('/')
      r = await self.client.request(
        'GET', BASE_URL,
        params={**self.params, 'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': from_sym, 'to_currency': to_sym},
      )
      r.raise_for_status()
      data: Any = r.json()
      _check_body_error(data)
      rate = data.get('Realtime Currency Exchange Rate', {}).get('5. Exchange Rate')
      return round_price(Decimal(rate)) if rate else None
    else:
      r = await self.client.request(
        'GET', BASE_URL,
        params={**self.params, 'function': id, 'interval': 'daily'},
      )
      r.raise_for_status()
      data = r.json()
      _check_body_error(data)
      for point in data.get('data', []):
        value = point.get('value', '.')
        if value != '.':
          return round_price(Decimal(value))
      return None

  async def current_price(self, id: str) -> Decimal | None:
    return await super().current_price(id)

  @wrap_exceptions
  async def historical_price(self, id: str, time: datetime) -> Price | None:
    date_str = time.strftime('%Y-%m-%d')
    if _is_forex(id):
      from_sym, to_sym = id.split('/')
      r = await self.client.request(
        'GET', BASE_URL,
        params={**self.params, 'function': 'FX_DAILY',
                'from_symbol': from_sym, 'to_symbol': to_sym,
                'outputsize': 'compact'},
      )
      r.raise_for_status()
      data: Any = r.json()
      _check_body_error(data)
      series = data.get('Time Series FX (Daily)', {})
      if entry := series.get(date_str):
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return Price(price=round_price(Decimal(entry['4. close'])), time=dt)
      return None
    else:
      r = await self.client.request(
        'GET', BASE_URL,
        params={**self.params, 'function': id, 'interval': 'daily'},
      )
      r.raise_for_status()
      data = r.json()
      _check_body_error(data)
      for point in data.get('data', []):
        if point.get('date') == date_str:
          value = point.get('value', '.')
          if value != '.':
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return Price(price=round_price(Decimal(value)), time=dt)
      return None

  async def historical_prices(self, ids: Sequence[str], time: datetime) -> Mapping[str, Price]:
    return await super().historical_prices(ids, time)

  async def market_cap(self, id: str) -> Decimal | None:
    raise NotImplementedError

  async def market_caps(self, ids: Sequence[str]) -> Mapping[str, Decimal]:
    return await super().market_caps(ids)
