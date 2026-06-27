from typing_extensions import Any, Literal, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import functools
import os

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
import httpx
from typed_core import HttpClient
from tribulnation.sdk import NetworkError, AuthError, RateLimited, ApiError

from .coingecko import batch, round_date, round_price
from .sdk import Pricing, Price


def _quote_symbol(quote: str) -> str:
  return quote.upper()

def _normalize_quote(data: Any) -> dict[str, Any]:
  if isinstance(data, Mapping):
    return {
      str(symbol).upper(): quote
      for symbol, quote in data.items()
      if isinstance(quote, Mapping)
    }

  if isinstance(data, list):
    out: dict[str, Any] = {}
    for quote in data:
      if isinstance(quote, Mapping) and quote.get('symbol'):
        out[str(quote['symbol']).upper()] = quote
    return out

  return {}


def _normalize_records(data: Any) -> list[Any]:
  if isinstance(data, list):
    return data
  if isinstance(data, Mapping):
    return list(data.values())
  return []


class CmcModel(BaseModel):
  model_config = ConfigDict(extra='ignore')


class CmcStatus(CmcModel):
  timestamp: datetime | None = None
  error_code: int | None = None
  error_message: str | None = None
  elapsed: int | None = None
  credit_count: int | None = None


class CmcQuote(CmcModel):
  price: Decimal
  market_cap: Decimal | None = None
  symbol: str | None = None
  timestamp: datetime | None = None
  last_updated: datetime | None = None


class CmcLatestAsset(CmcModel):
  id: int
  quote: dict[str, CmcQuote]

  @field_validator('quote', mode='before')
  @classmethod
  def normalize_quote(cls, value: Any) -> dict[str, Any]:
    return _normalize_quote(value)


class CmcLatestResponse(CmcModel):
  data: list[CmcLatestAsset]
  status: CmcStatus | None = None

  @field_validator('data', mode='before')
  @classmethod
  def normalize_data(cls, value: Any) -> list[Any]:
    return _normalize_records(value)


class CmcHistoricalQuote(CmcModel):
  timestamp: datetime
  quote: dict[str, CmcQuote]

  @field_validator('quote', mode='before')
  @classmethod
  def normalize_quote(cls, value: Any) -> dict[str, Any]:
    return _normalize_quote(value)


class CmcHistoricalAsset(CmcModel):
  id: int
  quotes: list[CmcHistoricalQuote]


class CmcHistoricalResponse(CmcModel):
  data: list[CmcHistoricalAsset]
  status: CmcStatus | None = None

  @field_validator('data', mode='before')
  @classmethod
  def normalize_data(cls, value: Any) -> list[Any]:
    return _normalize_records(value)


def _error_message(response: httpx.Response) -> str:
  try:
    payload = response.json()
  except ValueError:
    return response.text

  if isinstance(payload, Mapping):
    status = payload.get('status')
    if isinstance(status, Mapping) and status.get('error_message'):
      return str(status['error_message'])
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

CoinMarketCapQuote = Literal['eur', 'usd']

@dataclass
class CoinMarketCapPricing(Pricing):
  quote: CoinMarketCapQuote
  base_url: str = field(kw_only=True, default='https://pro-api.coinmarketcap.com')
  headers: Mapping[str, str] = field(kw_only=True, repr=False)
  client: HttpClient = field(kw_only=True, default_factory=HttpClient)

  async def __aenter__(self):
    await self.client.__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.client.__aexit__(exc_type, exc_value, traceback)

  @classmethod
  def new(cls, *, api_key: str | None = None, quote: CoinMarketCapQuote):
    api_key = api_key or os.environ.get('COINMARKETCAP_API_KEY')
    headers = {'Accept': 'application/json'}
    if api_key:
      headers['X-CMC_PRO_API_KEY'] = api_key
    return cls(quote=quote, headers=headers)

  @wrap_exceptions
  async def current_prices(self, ids: Sequence[str]) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for ids_batch in batch(ids, 100):
      r = await self.client.request(
        'GET', f'{self.base_url}/v3/cryptocurrency/quotes/latest',
        headers=self.headers,
        params={
          'id': ','.join(ids_batch),
          'convert': _quote_symbol(self.quote),
          'skip_invalid': 'true',
        },
      )
      r.raise_for_status()
      data = CmcLatestResponse.model_validate(r.json())

      for coin in data.data:
        quote = coin.quote.get(_quote_symbol(self.quote))
        if quote is not None:
          out[str(coin.id)] = round_price(quote.price)
    return out

  @wrap_exceptions
  async def market_caps(self, ids: Sequence[str]) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for ids_batch in batch(ids, 100):
      r = await self.client.request(
        'GET', f'{self.base_url}/v3/cryptocurrency/quotes/latest',
        headers=self.headers,
        params={
          'id': ','.join(ids_batch),
          'convert': _quote_symbol(self.quote),
          'skip_invalid': 'true',
        },
      )
      r.raise_for_status()
      data = CmcLatestResponse.model_validate(r.json())

      for coin in data.data:
        quote = coin.quote.get(_quote_symbol(self.quote))
        if quote is not None and quote.market_cap is not None:
          out[str(coin.id)] = round(quote.market_cap, 2)
    return out

  @wrap_exceptions
  async def historical_price(self, id: str, time: datetime) -> Price | None:
    date = round_date(time)
    if date.tzinfo is None:
      date = date.replace(tzinfo=timezone.utc)

    r = await self.client.request(
      'GET', f'{self.base_url}/v3/cryptocurrency/quotes/historical',
      headers=self.headers,
      params={
        'id': id,
        'time_start': date.isoformat(),
        'time_end': (date + timedelta(minutes=5)).isoformat(),
        'interval': '5m',
        'convert': _quote_symbol(self.quote),
        'skip_invalid': 'true',
      },
    )
    r.raise_for_status()
    data = CmcHistoricalResponse.model_validate(r.json())
    if not data.data:
      return None

    quotes = data.data[0].quotes
    if not quotes:
      return None

    quote = quotes[0]
    value = quote.quote.get(_quote_symbol(self.quote))
    if value is None:
      return None

    return Price(price=round_price(value.price), time=value.timestamp or quote.timestamp)
