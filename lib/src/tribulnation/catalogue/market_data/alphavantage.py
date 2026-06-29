from typing_extensions import Literal, Mapping, Any
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import functools
import os

import httpx
from tribulnation.sdk import NetworkError, AuthError, RateLimited, ApiError
from typed_core import HttpClient
from typed_core import exceptions as core_exc

from .coingecko import round_price
from .sdk import Pricing, Price


BASE_URL = 'https://www.alphavantage.co/query'

# Supported commodity function names
COMMODITY_FUNCTIONS = {
  'WTI', 'BRENT', 'NATURAL_GAS', 'COPPER', 'ALUMINUM',
  'WHEAT', 'CORN', 'COTTON', 'SUGAR', 'COFFEE',
}

AlphaVantageQuote = Literal['USD']


def _parse_id(id: str) -> tuple[str, str]:
  kind, sep, value = id.partition(':')
  if not sep or not value:
    raise ApiError(f'Invalid Alpha Vantage ID: {id!r}')
  if kind not in {'forex', 'stock', 'commodity'}:
    raise ApiError(f'Unsupported Alpha Vantage ID kind: {kind!r}')
  if kind == 'commodity' and value not in COMMODITY_FUNCTIONS:
    raise ApiError(f'Unsupported Alpha Vantage commodity function: {value!r}')
  return kind, value


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
    except core_exc.NetworkError as e:
      raise NetworkError(*e.args) from e
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
  def new(cls, *, api_key: str | None = None, quote: str = 'USD'):
    if quote != 'USD':
      raise ValueError('Alpha Vantage pricing only supports USD quotes')
    api_key = api_key or os.environ.get('ALPHAVANTAGE_API_KEY')
    params: dict[str, str] = {}
    if api_key:
      params['apikey'] = api_key
    return cls(quote='USD', params=params)

  @wrap_exceptions
  async def current_price(self, id: str) -> Decimal | None:
    kind, value = _parse_id(id)
    if kind == 'forex':
      if value == 'USD':
        return Decimal('1')
      r = await self.client.request(
        'GET', BASE_URL,
        params={**self.params, 'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': value, 'to_currency': 'USD'},
      )
      r.raise_for_status()
      data: Any = r.json()
      _check_body_error(data)
      rate = data.get('Realtime Currency Exchange Rate', {}).get('5. Exchange Rate')
      if rate:
        return round_price(Decimal(rate))

    elif kind == 'stock':
      r = await self.client.request(
        'GET', BASE_URL,
        params={**self.params, 'function': 'GLOBAL_QUOTE', 'symbol': value},
      )
      r.raise_for_status()
      data: Any = r.json()
      _check_body_error(data)
      price = data.get('Global Quote', {}).get('05. price')
      if price:
        return round_price(Decimal(price))

    else:
      r = await self.client.request(
        'GET', BASE_URL,
        params={**self.params, 'function': value, 'interval': 'daily'},
      )
      r.raise_for_status()
      data = r.json()
      _check_body_error(data)
      for point in data.get('data', []):
        point_value = point.get('value', '.')
        if point_value != '.':
          return round_price(Decimal(point_value))

  @wrap_exceptions
  async def historical_price(self, id: str, time: datetime) -> Price | None:
    date_str = time.strftime('%Y-%m-%d')
    kind, value = _parse_id(id)
    if kind == 'forex':
      if value == 'USD':
        return Price(price=Decimal('1'), time=time)
      r = await self.client.request(
        'GET', BASE_URL,
        params={**self.params, 'function': 'FX_DAILY',
                'from_symbol': value, 'to_symbol': 'USD',
                'outputsize': 'compact'},
      )
      r.raise_for_status()
      data: Any = r.json()
      _check_body_error(data)
      series = data.get('Time Series FX (Daily)', {})
      if entry := series.get(date_str):
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return Price(price=round_price(Decimal(entry['4. close'])), time=dt)

    elif kind == 'stock':
      r = await self.client.request(
        'GET', BASE_URL,
        params={**self.params, 'function': 'TIME_SERIES_DAILY',
                'symbol': value, 'outputsize': 'compact'},
      )
      r.raise_for_status()
      data: Any = r.json()
      _check_body_error(data)
      series = data.get('Time Series (Daily)', {})
      if entry := series.get(date_str):
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return Price(price=round_price(Decimal(entry['4. close'])), time=dt)

    else:
      r = await self.client.request(
        'GET', BASE_URL,
        params={**self.params, 'function': value, 'interval': 'daily'},
      )
      r.raise_for_status()
      data = r.json()
      _check_body_error(data)
      for point in data.get('data', []):
        if point.get('date') == date_str:
          point_value = point.get('value', '.')
          if point_value != '.':
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return Price(price=round_price(Decimal(point_value)), time=dt)

  async def market_cap(self, id: str) -> Decimal | None:
    raise NotImplementedError
