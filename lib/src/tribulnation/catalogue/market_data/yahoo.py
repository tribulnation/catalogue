"""Yahoo Finance pricing adapter."""

from typing_extensions import Collection, Literal, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from urllib.parse import quote as url_quote
import functools

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError
from tribulnation.sdk import SDK, NetworkError, RateLimited, ApiError
from typed_core import HttpClient
from typed_core import exceptions as core_exc

from .util import batch, round_price
from .sdk import Pricing, Price, Stats

COOKIE_URL = 'https://fc.yahoo.com'
CRUMB_URL = 'https://query2.finance.yahoo.com/v1/test/getcrumb'
QUOTE_URL = 'https://query2.finance.yahoo.com/v7/finance/quote'
CHART_URL = 'https://query1.finance.yahoo.com/v8/finance/chart'

YahooQuote = Literal['USD']

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


class YhChartResult(YhModel):
  """Single chart result entry."""
  timestamp: list[int] = []
  indicators: YhChartIndicators = YhChartIndicators()


class YhChartResponse(YhModel):
  """Top-level chart endpoint response."""
  result: list[YhChartResult] = []


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
  async def _fetch_quotes(self, symbols: Sequence[str]) -> dict[str, Stats]:
    """Fetch current price and market cap for a batch of symbols."""
    await self._ensure_crumb()
    r = await self.client.request(
      'GET', QUOTE_URL,
      params={'symbols': ','.join(symbols), 'crumb': self._crumb},
      headers=_HEADERS,
      cookies=self._cookies,
    )
    r.raise_for_status()
    data = r.json()
    response = YhQuoteResponse.model_validate(data.get('quoteResponse', {}))
    out: dict[str, Stats] = {}
    for item in response.result:
      market_cap = Decimal(item.marketCap) if item.marketCap is not None else None
      out[item.symbol] = Stats(
        price=round_price(item.regularMarketPrice),
        market_cap=round(market_cap, 2) if market_cap is not None else None,
      )
    return out

  async def current_stats(self, ids: Collection[str]) -> dict[str, Stats]:
    """Fetch current stats in batches."""
    if not ids:
      return {}
    out: dict[str, Stats] = {}
    for ids_batch in batch(list(ids), 20):
      out.update(await self._fetch_quotes(ids_batch))
    return out

  @SDK.method
  @wrap_exceptions
  async def historical_price(self, id: str, time: datetime) -> Price | None:
    """Fetch the closing price for a specific date using the chart API.

    Args:
      id: Yahoo ticker symbol.
      time: Target date/time.
    """
    target = time.date() if hasattr(time, 'date') else time
    target_dt = datetime(target.year, target.month, target.day, tzinfo=UTC)
    period1 = int((target_dt - timedelta(days=1)).timestamp())
    period2 = int((target_dt + timedelta(days=2)).timestamp())
    r = await self.client.request(
      'GET', f'{CHART_URL}/{url_quote(id, safe="")}',
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
    if not chart.result:
      return None
    result = chart.result[0]
    if not result.timestamp:
      return None
    closes = result.indicators.quote[0].close if result.indicators.quote else []
    adj_closes = result.indicators.adjclose[0].adjclose if result.indicators.adjclose else []
    target_str = target.isoformat()
    for i, ts in enumerate(result.timestamp):
      obs_date = datetime.fromtimestamp(ts, UTC).date()
      if obs_date.isoformat() != target_str:
        continue
      adj = adj_closes[i] if i < len(adj_closes) else None
      close = closes[i] if i < len(closes) else None
      price = adj or close
      if price is not None:
        return Price(price=round_price(price), time=datetime(obs_date.year, obs_date.month, obs_date.day))
    return None
