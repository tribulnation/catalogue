"""Yahoo Finance pricing adapter.

Yahoo quotes every listing in its own trading currency (the `currency` field),
e.g. TWD for `2330.TW`. Prices and market caps in any other currency than the
requested quote are converted with Yahoo's own `{CCY}{QUOTE}=X` rate, which
gives the quote currency per one unit of `CCY` (`TWDUSD=X` ≈ 0.0314), so the
conversion is a multiplication. A value whose rate is unavailable is omitted,
never returned in its local currency.
"""

from typing_extensions import Collection, Iterable, Literal, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from urllib.parse import quote as url_quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import functools
import logging

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError
from tribulnation.sdk import SDK, Error, NetworkError, RateLimited, ApiError
from typed_core import HttpClient
from typed_core import exceptions as core_exc

from .util import batch
from .sdk import Pricing, Price, Stats

COOKIE_URL = 'https://fc.yahoo.com'
CRUMB_URL = 'https://query2.finance.yahoo.com/v1/test/getcrumb'
QUOTE_URL = 'https://query2.finance.yahoo.com/v7/finance/quote'
CHART_URL = 'https://query1.finance.yahoo.com/v8/finance/chart'

YahooQuote = Literal['USD']

MINOR_UNITS: dict[str, tuple[str, int]] = {
  'GBp': ('GBP', 100),
  'GBX': ('GBP', 100),
  'ZAc': ('ZAR', 100),
  'ZAC': ('ZAR', 100),
  'ILA': ('ILS', 100),
}
"""Yahoo minor-unit currency codes: (ISO currency, minor units per major unit).

Only the price is in minor units. Yahoo reports `marketCap` in the major currency:
`VOD.L` quotes 123.9 GBp with a 28.6B (GBP) market cap.
"""

logger = logging.getLogger('tribulnation.catalogue')

_HEADERS = {
  'Accept': 'application/json',
  'User-Agent': 'Mozilla/5.0',
}


class YhModel(BaseModel):
  """Base model for Yahoo Finance responses."""
  model_config = ConfigDict(extra='ignore')


class YhQuoteItem(YhModel):
  """Single quote result."""
  symbol: str
  currency: str | None = None
  """Currency `regularMarketPrice` and `marketCap` are quoted in, possibly a minor unit."""
  regularMarketPrice: Decimal
  marketCap: int | None = None


class YhQuoteResponse(YhModel):
  """Top-level quote endpoint response."""
  result: list[YhQuoteItem] = []


class YhChartOHLCV(YhModel):
  """OHLCV quote data from chart endpoint."""
  close: list[Decimal | None] = []


class YhChartAdjClose(YhModel):
  """Adjusted close data from chart endpoint."""
  adjclose: list[Decimal | None] = []


class YhChartIndicators(YhModel):
  """Chart indicators container."""
  quote: list[YhChartOHLCV] = []
  adjclose: list[YhChartAdjClose] = []


class YhChartMeta(YhModel):
  """Chart metadata."""
  currency: str | None = None
  """Currency the chart's prices are quoted in, possibly a minor unit."""
  exchangeTimezoneName: str | None = None
  """IANA time zone of the exchange; daily bars start at its local midnight or open."""
  gmtoffset: int = 0
  """Exchange offset from UTC in seconds at request time, used when the zone is unknown."""


class YhChartResult(YhModel):
  """Single chart result entry."""
  meta: YhChartMeta = YhChartMeta()
  timestamp: list[int] = []
  indicators: YhChartIndicators = YhChartIndicators()


class YhChartResponse(YhModel):
  """Top-level chart endpoint response."""
  result: list[YhChartResult] = []


def split_currency(currency: str) -> tuple[str, int]:
  """Map a Yahoo currency code to its ISO currency and minor units per major unit."""
  return MINOR_UNITS.get(currency, (currency, 1))


def fx_symbol(currency: str, quote: str) -> str:
  """Yahoo symbol for the rate giving `quote` per one unit of `currency`."""
  return f'{currency}{quote}=X'


def local_date(ts: int, meta: YhChartMeta) -> date:
  """Exchange-local date of a bar timestamp.

  FX bars start at London midnight, 23:00 UTC in summer, so their UTC date is
  the previous day.
  """
  if meta.exchangeTimezoneName:
    try:
      return datetime.fromtimestamp(ts, ZoneInfo(meta.exchangeTimezoneName)).date()
    except (ZoneInfoNotFoundError, ValueError):
      pass
  return datetime.fromtimestamp(ts + meta.gmtoffset, UTC).date()


def chart_value(result: YhChartResult, target: date) -> tuple[Decimal, date] | None:
  """Return the (adjusted) close of the bar on `target`, in the exchange's local date."""
  closes = result.indicators.quote[0].close if result.indicators.quote else []
  adj_closes = result.indicators.adjclose[0].adjclose if result.indicators.adjclose else []
  for i, ts in enumerate(result.timestamp):
    obs_date = local_date(ts, result.meta)
    if obs_date != target:
      continue
    adj = adj_closes[i] if i < len(adj_closes) else None
    close = closes[i] if i < len(closes) else None
    price = adj or close
    if price is not None:
      return price, obs_date
  return None


def _error_message(response: httpx.Response) -> str:
  """Extract an error message from a Yahoo Finance response."""
  try:
    payload = response.json()
  except ValueError:
    return response.text
  if isinstance(payload, dict):
    for key in ('chart', 'quoteResponse', 'finance'):
      section = payload.get(key, {})
      if isinstance(section, dict) and section.get('error'):
        err = section['error']
        if isinstance(err, dict):
          return str(err.get('description', err.get('code', response.text)))
  return response.text


def wrap_exceptions(f):
  """Map transport and validation errors to SDK exceptions."""
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
    except ValidationError as e:
      raise ApiError(*e.args) from e
  return wrapper


@dataclass
class YahooPricing(Pricing):
  """Yahoo Finance pricing source (no API key required, USD only)."""
  quote: YahooQuote
  client: HttpClient = field(kw_only=True, default_factory=HttpClient)
  _crumb: str | None = field(default=None, init=False, repr=False)
  _cookies: dict[str, str] = field(default_factory=dict, init=False, repr=False)

  async def __aenter__(self):
    await self.client.__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.client.__aexit__(exc_type, exc_value, traceback)

  @classmethod
  def new(cls, *, quote: str = 'USD'):
    """Create a new Yahoo Finance pricing client.

    Args:
      quote: Quote currency. Only USD is supported.
    """
    if quote.upper() != 'USD':
      raise ValueError('Yahoo pricing only supports USD quotes')
    return cls(quote='USD')

  async def _ensure_crumb(self):
    """Fetch a session cookie and crumb token for the quote endpoint."""
    if self._crumb is not None:
      return
    browser_headers = {'User-Agent': _HEADERS['User-Agent']}
    r = await self.client.request('GET', COOKIE_URL, headers=browser_headers)
    self._cookies = dict(r.cookies)
    r2 = await self.client.request('GET', CRUMB_URL, headers=browser_headers, cookies=self._cookies)
    if r2.status_code != 200 or not r2.text.strip():
      raise ApiError(f'Failed to fetch Yahoo crumb: {r2.status_code}')
    self._crumb = r2.text.strip()

  @SDK.method
  @wrap_exceptions
  async def _fetch_quotes(self, symbols: Sequence[str]) -> list[YhQuoteItem]:
    """Fetch raw quotes for a batch of symbols, in each listing's own currency."""
    await self._ensure_crumb()
    r = await self.client.request(
      'GET', QUOTE_URL,
      params={'symbols': ','.join(symbols), 'crumb': self._crumb},
      headers=_HEADERS,
      cookies=self._cookies,
    )
    r.raise_for_status()
    data = r.json()
    return YhQuoteResponse.model_validate(data.get('quoteResponse', {})).result

  async def _fetch_all_quotes(self, symbols: Iterable[str]) -> list[YhQuoteItem]:
    """Fetch raw quotes in batches of 20 symbols."""
    items: list[YhQuoteItem] = []
    for symbols_batch in batch(list(symbols), 20):
      items.extend(await self._fetch_quotes(symbols_batch))
    return items

  async def _fx_rates(self, currencies: Collection[str]) -> dict[str, Decimal]:
    """Fetch `quote` per one unit of each ISO currency.

    Missing rates are left out. A failed request leaves every rate out rather than
    failing the batch, so listings already in the quote currency keep their prices.
    """
    if not currencies:
      return {}
    symbols = {fx_symbol(ccy, self.quote): ccy for ccy in currencies}
    try:
      items = await self._fetch_all_quotes(symbols)
    except Error as e:
      logger.warning('Failed to fetch Yahoo FX rates %s: %s', ', '.join(symbols), e)
      return {}
    rates: dict[str, Decimal] = {}
    for item in items:
      ccy = symbols.get(item.symbol)
      if ccy is not None and item.currency == self.quote and item.regularMarketPrice > 0:
        rates[ccy] = item.regularMarketPrice
    return rates

  async def current_stats(self, ids: Collection[str]) -> dict[str, Stats]:
    """Fetch current stats in batches, converted to the quote currency.

    Listings quoted in another currency are converted with Yahoo's FX rate for
    that currency, fetched in one extra batch. Listings without a currency or
    without an available rate are omitted.
    """
    if not ids:
      return {}
    items = await self._fetch_all_quotes(ids)
    foreign = {
      split_currency(item.currency)[0]
      for item in items if item.currency is not None and item.currency != self.quote
    }
    rates = await self._fx_rates(foreign)
    out: dict[str, Stats] = {}
    for item in items:
      if item.currency is None:
        logger.warning('Yahoo quote for %s has no currency; omitted', item.symbol)
        continue
      price = item.regularMarketPrice
      market_cap = Decimal(item.marketCap) if item.marketCap is not None else None
      if item.currency != self.quote:
        ccy, units = split_currency(item.currency)
        if (rate := rates.get(ccy)) is None:
          logger.warning('No %s rate for %s (%s); omitted', fx_symbol(ccy, self.quote), item.symbol, item.currency)
          continue
        price = price * rate / units
        market_cap = market_cap * rate if market_cap is not None else None
      out[item.symbol] = Stats(
        price=price,
        market_cap=round(market_cap, 2) if market_cap is not None else None,
      )
    return out

  async def _fetch_chart(self, symbol: str, *, period1: int, period2: int) -> YhChartResult | None:
    """Fetch daily bars for `symbol` between two UNIX timestamps."""
    r = await self.client.request(
      'GET', f'{CHART_URL}/{url_quote(symbol, safe="")}',
      params={
        'period1': str(period1),
        'period2': str(period2),
        'interval': '1d',
        'events': 'history',
        'includeAdjustedClose': 'true',
      },
      headers=_HEADERS,
    )
    r.raise_for_status()
    data = r.json()
    chart = YhChartResponse.model_validate(data.get('chart', {}))
    return chart.result[0] if chart.result else None

  @SDK.method
  @wrap_exceptions
  async def historical_price(self, id: str, time: datetime) -> Price | None:
    """Fetch the closing price for a specific date using the chart API.

    A close in another currency is converted with that day's close of Yahoo's
    FX rate; without one, the price is `None`.

    Args:
      id: Yahoo ticker symbol.
      time: Target date/time.
    """
    target = time.date() if hasattr(time, 'date') else time
    target_dt = datetime(target.year, target.month, target.day, tzinfo=UTC)
    period1 = int((target_dt - timedelta(days=1)).timestamp())
    period2 = int((target_dt + timedelta(days=2)).timestamp())
    result = await self._fetch_chart(id, period1=period1, period2=period2)
    if result is None or (found := chart_value(result, target)) is None:
      return None
    price, obs_date = found
    currency = result.meta.currency
    if currency is None:
      logger.warning('Yahoo chart for %s has no currency; omitted', id)
      return None
    if currency != self.quote:
      ccy, units = split_currency(currency)
      fx = await self._fetch_chart(fx_symbol(ccy, self.quote), period1=period1, period2=period2)
      fx_value = chart_value(fx, obs_date) if fx is not None and fx.meta.currency == self.quote else None
      if fx_value is None:
        logger.warning('No %s rate on %s for %s (%s); omitted', fx_symbol(ccy, self.quote), obs_date, id, currency)
        return None
      price = price * fx_value[0] / units
    return Price(price=price, time=datetime(obs_date.year, obs_date.month, obs_date.day))
