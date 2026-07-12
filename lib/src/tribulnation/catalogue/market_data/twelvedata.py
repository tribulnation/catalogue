from typing_extensions import Literal, Collection, Mapping, Any
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import functools
import os

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError
from tribulnation.sdk import NetworkError, AuthError, RateLimited, ApiError
from typed_core import HttpClient

from .util import round_price
from .sdk import Pricing, Price, Stats


BASE_URL = 'https://api.twelvedata.com'

TwelveDataQuote = Literal['USD', 'EUR']


class TdModel(BaseModel):
  model_config = ConfigDict(extra='ignore')


class TdPrice(TdModel):
  price: Decimal


class TdOHLCV(TdModel):
  datetime: str
  close: Decimal


class TdTimeSeries(TdModel):
  values: list[TdOHLCV] = []
  status: str = 'ok'
  message: str | None = None


def _parse_dt(s: str) -> datetime:
  if len(s) == 10:
    return datetime.strptime(s, '%Y-%m-%d')
  return datetime.fromisoformat(s)


def _raise_body_error(data: Any) -> None:
  message = str(data.get('message', 'Unknown error'))
  code = data.get('code', 0)
  if code == 401:
    raise AuthError(message)
  if code == 429:
    raise RateLimited(message)
  raise ApiError(message)


def _error_message(response: httpx.Response) -> str:
  try:
    payload = response.json()
  except ValueError:
    return response.text
  if isinstance(payload, Mapping) and payload.get('message'):
    return str(payload['message'])
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
class TwelveDataPricing(Pricing):
  quote: TwelveDataQuote
  params: dict[str, str] = field(kw_only=True, repr=False)
  client: HttpClient = field(kw_only=True, default_factory=HttpClient)

  async def __aenter__(self):
    await self.client.__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.client.__aexit__(exc_type, exc_value, traceback)

  @classmethod
  def new(cls, *, api_key: str | None = None, quote: TwelveDataQuote = 'USD'):
    api_key = api_key or os.environ.get('TWELVEDATA_API_KEY')
    params: dict[str, str] = {}
    if api_key:
      params['apikey'] = api_key
    return cls(quote=quote, params=params)

  @wrap_exceptions
  async def current_stats(self, ids: Collection[str]) -> dict[str, Stats]:
    if not ids:
      return {}
    r = await self.client.request(
      'GET', f'{BASE_URL}/price',
      params={**self.params, 'symbol': ','.join(ids)},
    )
    r.raise_for_status()
    data: Any = r.json()

    out: dict[str, Stats] = {}
    if len(ids) == 1:
      id = next(iter(ids))
      # Single symbol: response is {price: "..."} or {code, message, status}
      if data.get('status') == 'error':
        _raise_body_error(data)
      if 'price' in data:
        out[id] = Stats(price=round_price(TdPrice.model_validate(data).price))
    else:
      # Multiple symbols: response is {symbol: {price: "..."}, ...}
      # Symbols with errors have {code, message, status} instead — skip them
      for symbol in ids:
        entry = data.get(symbol)
        if isinstance(entry, Mapping) and 'price' in entry:
          out[symbol] = Stats(price=round_price(TdPrice.model_validate(entry).price))
    return out


  @wrap_exceptions
  async def historical_price(self, id: str, time: datetime) -> Price | None:
    date_str = time.strftime('%Y-%m-%d')
    r = await self.client.request(
      'GET', f'{BASE_URL}/time_series',
      params={
        **self.params,
        'symbol': id,
        'interval': '1day',
        'start_date': date_str,
        'end_date': date_str,
        'outputsize': '1',
      },
    )
    r.raise_for_status()
    data = TdTimeSeries.model_validate(r.json())
    if not data.values:
      return None
    entry = data.values[0]
    return Price(price=round_price(entry.close), time=_parse_dt(entry.datetime))
