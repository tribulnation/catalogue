from typing_extensions import Collection, Literal, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import csv
import functools
import re
import xml.etree.ElementTree as ET

import httpx
from tribulnation.sdk import SDK, NetworkError, RateLimited, ApiError
from typed_core import HttpClient
from typed_core import exceptions as core_exc

from .sdk import Pricing, Price, Stats


DAILY_URL = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
"""Latest euro foreign exchange reference rates (only currencies ECB still publishes)."""
DATA_URL = 'https://data-api.ecb.europa.eu/service/data/EXR'
"""ECB Data Portal, `EXR` dataset; series key `D.<currency>.EUR.SP00.A`."""

EcbQuote = Literal['USD', 'EUR']

_code = re.compile(r'^[A-Z]{3}$')


def _parse_id(id: str) -> str:
  if not _code.fullmatch(id):
    raise ApiError(f'Invalid ISO 4217 code: {id!r}')
  return id


def _convert(rates: Mapping[str, Decimal], ids: Collection[str], quote: str) -> dict[str, Decimal]:
  """Turn ECB rates (units of currency per 1 EUR) into prices of each ID in `quote`."""
  rates = {**rates, 'EUR': Decimal(1)}
  if (quote_rate := rates.get(quote)) is None:
    return {}
  return {id: quote_rate / rates[id] for id in ids if rates.get(id)}


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
      if status == 429:
        raise RateLimited(e.response.text) from e
      raise ApiError(e.response.text) from e
  return wrapper


@dataclass
class EcbPricing(Pricing):
  """ECB euro foreign exchange reference rates, keyed by ISO 4217 code."""
  quote: EcbQuote
  client: HttpClient = field(kw_only=True, default_factory=HttpClient)

  async def __aenter__(self):
    await self.client.__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.client.__aexit__(exc_type, exc_value, traceback)

  @classmethod
  def new(cls, *, quote: str = 'USD'):
    q = quote.upper()
    if q not in ('USD', 'EUR'):
      raise ValueError('ECB pricing only supports USD and EUR quotes')
    return cls(quote=q) # type: ignore

  @SDK.method
  @wrap_exceptions
  async def _daily(self) -> tuple[datetime, dict[str, Decimal]]:
    r = await self.client.request('GET', DAILY_URL)
    r.raise_for_status()
    try:
      root = ET.fromstring(r.text)
    except ET.ParseError as e:
      raise ApiError(f'Invalid ECB daily XML: {e}') from e
    day = next((c for c in root.iter() if c.tag.endswith('Cube') and 'time' in c.attrib), None)
    if day is None:
      raise ApiError('ECB daily XML has no dated Cube')
    try:
      time = datetime.strptime(day.attrib['time'], '%Y-%m-%d')
      rates = {c.attrib['currency']: Decimal(c.attrib['rate']) for c in day if 'currency' in c.attrib}
    except Exception as e:
      raise ApiError(f'Invalid ECB daily rates: {e}') from e
    return time, rates

  @SDK.method
  @wrap_exceptions
  async def _observations(self, codes: Collection[str], date: str) -> dict[str, Decimal]:
    key = 'D.' + '+'.join(sorted(codes)) + '.EUR.SP00.A'
    r = await self.client.request('GET', f'{DATA_URL}/{key}', params={
      'startPeriod': date, 'endPeriod': date, 'format': 'csvdata',
    })
    r.raise_for_status()
    rates: dict[str, Decimal] = {}
    for row in csv.DictReader(r.text.splitlines()):
      if row.get('TIME_PERIOD') != date or row.get('OBS_VALUE') in {None, '', 'NaN'}:
        continue
      try:
        rates[row['CURRENCY']] = Decimal(row['OBS_VALUE'])
      except Exception as e:
        raise ApiError(f'Invalid ECB observation for {row.get("CURRENCY")}: {row.get("OBS_VALUE")!r}') from e
    return rates

  async def current_stats(self, ids: Collection[str]) -> Mapping[str, Stats]:
    ids = [_parse_id(id) for id in ids]
    _, rates = await self._daily()
    return {id: Stats(price=price) for id, price in _convert(rates, ids, self.quote).items()}

  async def historical_price(self, id: str, time: datetime) -> Price | None:
    id = _parse_id(id)
    codes = {id, self.quote} - {'EUR'}
    date = time.date()
    rates = await self._observations(codes, date.isoformat()) if codes else {}
    if (price := _convert(rates, [id], self.quote).get(id)) is not None:
      return Price(price=price, time=datetime(date.year, date.month, date.day))
    return None
