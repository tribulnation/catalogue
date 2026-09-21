"""Public DefiLlama token prices, with optional daily FRED EUR conversion."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
import json
from urllib.parse import quote as url_quote

from pydantic import Field, TypeAdapter
from tribulnation.sdk import ApiError, SDK
from typed_core import HttpClient
from typing_extensions import Annotated, Collection, NotRequired, TypedDict

from .fred import FredPricing, wrap_exceptions
from .sdk import Price, Pricing, Quote, Stats
from .util import batch

BASE_URL = 'https://coins.llama.fi/prices'


class CoinPrice(TypedDict):
  """Optional observations returned for one DefiLlama token identifier."""

  price: NotRequired[Annotated[Decimal, Field(ge=0, allow_inf_nan=False)] | None]
  timestamp: NotRequired[int | None]


class PricesResponse(TypedDict):
  """DefiLlama response keyed by chain/address or coingecko-prefixed IDs."""

  coins: dict[str, CoinPrice]


RESPONSE = TypeAdapter(PricesResponse)


def observation_time(timestamp: int) -> datetime:
  """Convert the provider's observation timestamp to an aware UTC datetime."""
  try:
    return datetime.fromtimestamp(timestamp, timezone.utc)
  except (ValueError, OverflowError, OSError) as error:
    raise ApiError(f'Invalid DefiLlama timestamp: {timestamp}') from error


def eur_rate(rates: list[tuple[datetime, Decimal]], day: date) -> Decimal | None:
  """Use the latest published USD-per-EUR rate on or before the price date."""
  available = [(time, rate) for time, rate in rates if time.date() <= day]
  if not available:
    return None
  _, rate = max(available, key=lambda observation: observation[0])
  if not rate.is_finite() or rate <= 0:
    raise ApiError('Invalid FRED USD-per-EUR exchange rate')
  return rate


@dataclass
class DefiLlamaPricing(Pricing):
  """Price tokens by DefiLlama ID without an API key.

  EUR quotes divide USD observations by the latest published daily DEXUSEU
  rate on or before the observation date. FRED publication can lag by several
  days; this is not an intraday FX quote. Market cap is unavailable.

  References:
    - [DefiLlama API](https://defillama.com/docs/api)
    - [FRED DEXUSEU](https://fred.stlouisfed.org/series/DEXUSEU)
  """

  quote: Quote = 'usd'
  client: HttpClient = field(kw_only=True, default_factory=HttpClient)

  def __post_init__(self):
    """Reject unsupported quotes even when constructing the dataclass directly."""
    if self.quote not in ('usd', 'eur'):
      raise ValueError('DefiLlama pricing supports USD or EUR quotes')

  @classmethod
  def new(cls, *, quote: Quote = 'usd') -> 'DefiLlamaPricing':
    """Construct a public pricing client for USD or EUR quotes."""
    return cls(quote=quote)

  async def __aenter__(self):
    """Open the shared token-price and exchange-rate HTTP transport."""
    await self.client.__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    """Close the shared HTTP transport."""
    await self.client.__aexit__(exc_type, exc_value, traceback)

  @SDK.method
  @wrap_exceptions
  async def fetch_prices(
    self, ids: Collection[str], *, timestamp: int | None = None
  ) -> dict[str, CoinPrice]:
    """Fetch a batch of USD prices and validate the wire response."""
    endpoint = 'current' if timestamp is None else f'historical/{timestamp}'
    coins = ','.join(url_quote(id, safe=':') for id in ids)
    response = await self.client.request('GET', f'{BASE_URL}/{endpoint}/{coins}')
    response.raise_for_status()
    try:
      return RESPONSE.validate_python(
        json.loads(response.content, parse_float=Decimal)
      )['coins']
    except ValueError as error:
      raise ApiError('Invalid DefiLlama price response') from error

  async def current_stats(self, ids: Collection[str]) -> dict[str, Stats]:
    """Fetch available token prices; omitted tokens remain absent."""
    prices: dict[str, CoinPrice] = {}
    for ids_batch in batch(list(dict.fromkeys(ids)), 100):
      response = await self.fetch_prices(ids_batch)
      prices.update({id: response[id] for id in ids_batch if id in response})
    rates = (
      await FredPricing(quote='USD', client=self.client)._observations('DEXUSEU')
      if prices and self.quote == 'eur'
      else []
    )
    result: dict[str, Stats] = {}
    for id, coin in prices.items():
      price = coin.get('price')
      if price is None:
        continue
      if self.quote == 'eur':
        timestamp = coin.get('timestamp')
        if timestamp is None:
          continue
        rate = eur_rate(rates, observation_time(timestamp).date())
        if rate is None:
          continue
        price /= rate
      result[id] = Stats(price=price)
    return result

  async def historical_price(self, id: str, time: datetime) -> Price | None:
    """Return the provider's observation, interpreting naive requests as UTC."""
    target = time if time.tzinfo is not None else time.replace(tzinfo=timezone.utc)
    coin = (await self.fetch_prices([id], timestamp=int(target.timestamp()))).get(id)
    if coin is None:
      return None
    price = coin.get('price')
    timestamp = coin.get('timestamp')
    if price is None or timestamp is None:
      return None
    observed = observation_time(timestamp)
    if self.quote == 'eur':
      rates = await FredPricing(quote='USD', client=self.client)._observations(
        'DEXUSEU'
      )
      rate = eur_rate(rates, observed.date())
      if rate is None:
        return None
      price /= rate
    return Price(price=price, time=observed)
