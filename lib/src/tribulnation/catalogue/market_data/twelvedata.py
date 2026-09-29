"""TwelveData pricing adapter.

TwelveData quotes each listing in its own currency: a bare `6525` resolves to the
Tokyo listing, in JPY. Stocks and funds carry that currency in `currency`; pairs
such as `EUR/USD` are quoted in the part after the slash. Values in any other
currency than the requested quote are omitted, never returned unconverted.
"""

from typing_extensions import Literal, Collection, Mapping, Sequence, Any
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import asyncio
import functools
import logging
import os

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError
from tribulnation.sdk import SDK, NetworkError, AuthError, RateLimited, ApiError
from typed_core import HttpClient

from .util import batch
from .sdk import Pricing, Price, Stats


BASE_URL = 'https://api.twelvedata.com'

TwelveDataQuote = Literal['USD', 'EUR']

logger = logging.getLogger('tribulnation.catalogue')


class TdModel(BaseModel):
  model_config = ConfigDict(extra='ignore')


class TdQuote(TdModel):
  """Latest quote of a symbol."""
  symbol: str
  currency: str | None = None
  """Listing currency. Absent for pairs, which are quoted in their second leg."""
  close: Decimal
  """Latest price: the close of the current daily bar."""


class TdTimeSeriesMeta(TdModel):
  """Time series metadata."""
  currency: str | None = None
  """Listing currency. Absent for pairs, which are quoted in their second leg."""


class TdOHLCV(TdModel):
  datetime: str
  close: Decimal


class TdTimeSeries(TdModel):
  meta: TdTimeSeriesMeta = TdTimeSeriesMeta()
  values: list[TdOHLCV] = []
  status: str = 'ok'
  message: str | None = None


def quote_currency(symbol: str, currency: str | None) -> str | None:
  """Currency a symbol is quoted in: its `currency`, or a pair's second leg."""
  if currency is not None:
    return currency
  if '/' in symbol:
    return symbol.rsplit('/', 1)[1]
  return None


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
  credits_per_minute: int = field(kw_only=True, default=8)
  """API credits allowed per minute. Each symbol costs 1 credit."""

  async def __aenter__(self):
    await self.client.__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.client.__aexit__(exc_type, exc_value, traceback)

  @classmethod
  def new(
    cls, *, api_key: str | None = None,
    quote: TwelveDataQuote = 'USD', credits_per_minute: int | None = None,
  ):
    """Create a new TwelveData pricing client.

    Args:
      api_key: API key. Falls back to TWELVEDATA_API_KEY env var.
      quote: Quote currency.
      credits_per_minute: Credits per minute. Falls back to TWELVEDATA_CREDITS_PER_MINUTE env var, then 8.
    """
    api_key = api_key or os.environ.get('TWELVEDATA_API_KEY')
    if credits_per_minute is None:
      credits_per_minute = int(os.environ.get('TWELVEDATA_CREDITS_PER_MINUTE', '8'))
    params: dict[str, str] = {}
    if api_key:
      params['apikey'] = api_key
    return cls(quote=quote, params=params, credits_per_minute=credits_per_minute)

  def _in_quote(self, symbol: str, currency: str | None) -> bool:
    """Whether `symbol` is quoted in the requested currency; logs when it is not."""
    ccy = quote_currency(symbol, currency)
    if ccy == self.quote:
      return True
    logger.warning('TwelveData %s is quoted in %s, not %s; omitted', symbol, ccy or 'an unknown currency', self.quote)
    return False

  @SDK.method
  @wrap_exceptions
  async def _fetch_prices(self, symbols: Sequence[str]) -> dict[str, Stats]:
    """Fetch latest prices for a single batch of symbols.

    Uses `/quote` rather than `/price` because only `/quote` states the currency.
    Both cost one credit per symbol.
    """
    r = await self.client.request(
      'GET', f'{BASE_URL}/quote',
      params={**self.params, 'symbol': ','.join(symbols)},
    )
    r.raise_for_status()
    data: Any = r.json()
    if len(symbols) == 1:
      if data.get('status') == 'error':
        _raise_body_error(data)
      entries = {symbols[0]: data}
    else:
      entries = {symbol: data.get(symbol) for symbol in symbols}
    out: dict[str, Stats] = {}
    for symbol, entry in entries.items():
      if isinstance(entry, Mapping) and 'close' in entry:
        quote = TdQuote.model_validate({**entry, 'symbol': symbol})
        if self._in_quote(symbol, quote.currency):
          out[symbol] = Stats(price=quote.close)
    return out

  async def current_stats(self, ids: Collection[str]) -> dict[str, Stats]:
    """Fetch prices in batches sized to the per-minute credit limit."""
    if not ids:
      return {}
    out: dict[str, Stats] = {}
    for i, ids_batch in enumerate(batch(list(ids), self.credits_per_minute)):
      if i > 0:
        await asyncio.sleep(60)
      out.update(await self._fetch_prices(ids_batch))
    return out

  @SDK.method
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
    if not data.values or not self._in_quote(id, data.meta.currency):
      return None
    entry = data.values[0]
    return Price(price=entry.close, time=_parse_dt(entry.datetime))
