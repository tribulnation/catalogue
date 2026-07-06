from typing_extensions import Any, Collection, Literal, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import csv
import functools

import httpx
from tribulnation.sdk import NetworkError, RateLimited, ApiError
from typed_core import HttpClient
from typed_core import exceptions as core_exc

from .coingecko import round_price
from .sdk import Pricing, Price, Stats


BASE_URL = 'https://fred.stlouisfed.org/graph/fredgraph.csv'

FredQuote = Literal['USD']


def _parse_id(id: str) -> tuple[str, str]:
  transform, sep, series_id = id.partition(':')
  if not sep:
    return 'identity', id
  if transform not in {'identity', 'inverse'}:
    raise ApiError(f'Unsupported FRED ID transform: {transform!r}')
  if not series_id:
    raise ApiError(f'Invalid FRED ID: {id!r}')
  return transform, series_id


def _apply_transform(value: Decimal, transform: str) -> Decimal:
  if transform == 'identity':
    return value
  if transform == 'inverse':
    if value == 0:
      raise ApiError('Cannot invert zero FRED observation')
    return Decimal('1') / value
  raise ApiError(f'Unsupported FRED transform: {transform!r}')


def _error_message(response: httpx.Response) -> str:
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
      if status == 429:
        raise RateLimited(message) from e
      raise ApiError(message) from e
  return wrapper


@dataclass
class FredPricing(Pricing):
  quote: FredQuote
  client: HttpClient = field(kw_only=True, default_factory=HttpClient)

  async def __aenter__(self):
    await self.client.__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.client.__aexit__(exc_type, exc_value, traceback)

  @classmethod
  def new(cls, *, quote: str = 'USD'):
    if quote.lower() != 'usd':
      raise ValueError('FRED pricing only supports USD quotes')
    return cls(quote='USD')

  async def _observations(self, id: str) -> list[tuple[datetime, Decimal]]:
    transform, series_id = _parse_id(id)
    r = await self.client.request('GET', BASE_URL, params={'id': series_id})
    r.raise_for_status()

    rows: list[tuple[datetime, Decimal]] = []
    reader = csv.DictReader(r.text.splitlines())
    if reader.fieldnames != ['observation_date', series_id]:
      raise ApiError(f'Unexpected FRED CSV header for {series_id}: {reader.fieldnames!r}')
    for row in reader:
      value = row.get(series_id)
      if value in {None, '', '.'}:
        continue
      try:
        price = _apply_transform(Decimal(value), transform) # type: ignore
      except Exception as e:
        raise ApiError(f'Invalid FRED observation for {series_id}: {value!r}') from e
      rows.append((datetime.strptime(row['observation_date'], '%Y-%m-%d'), round_price(price)))
    return rows

  @wrap_exceptions
  async def current_stats(self, ids: Collection[str]) -> Mapping[str, Stats]:
    out: dict[str, Stats] = {}
    for id in ids:
      observations = await self._observations(id)
      if observations:
        out[id] = Stats(price=observations[-1][1])
    return out

  @wrap_exceptions
  async def historical_price(self, id: str, time: datetime) -> Price | None:
    date = time.date()
    for observation_time, price in await self._observations(id):
      if observation_time.date() == date:
        return Price(price=price, time=observation_time)
    return None
