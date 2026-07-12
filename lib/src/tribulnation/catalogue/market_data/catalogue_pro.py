from typing_extensions import Collection, Mapping, TypedDict, NotRequired
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import os

import pydantic
from tribulnation.sdk import SDK, AuthError, ApiError, BadRequest, RateLimited
from typed_core import HttpClient
import httpx

from .sdk import Pricing, Price, Stats
from .coingecko import round_date

CATALOGUE_PRO_API_BASE_URL = 'https://catalogue-pro.tribulnation.com'

class StatsReply(TypedDict):
  price_usd: Decimal
  market_cap_usd: NotRequired[Decimal|None]

stats_adapter = pydantic.TypeAdapter(StatsReply)
latest_adapter = pydantic.TypeAdapter(Mapping[str, StatsReply])


def raise_on_error(r: httpx.Response):
  if r.status_code == 401:
    raise AuthError(r.text)
  elif r.status_code == 429:
    raise RateLimited(r.text)
  elif 400 <= r.status_code < 500:
    raise BadRequest(r.text)
  elif 500 <= r.status_code < 600:
    raise ApiError(r.text)
  
@dataclass
class CatalogueProPricing(Pricing):
  base_url: str
  api_key: str = field(repr=False)
  client: HttpClient = field(kw_only=True, default_factory=HttpClient)

  @property
  def headers(self) -> dict[str, str]:
    return {'Authorization': f'Bearer {self.api_key}'}

  async def __aenter__(self):
    await self.client.__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.client.__aexit__(exc_type, exc_value, traceback)

  @classmethod
  def new(cls, *, base_url: str | None = None, api_key: str | None = None):
    base_url = base_url or os.environ.get('CATALOGUE_PRO_API_BASE_URL', CATALOGUE_PRO_API_BASE_URL)
    api_key = api_key or os.environ.get('CATALOGUE_PRO_API_KEY', '')
    if not api_key:
      raise ValueError('CATALOGUE_PRO_API_KEY is required')
    return cls(base_url=base_url, api_key=api_key)

  @SDK.method
  async def current_stats(self, ids: Collection[str]) -> Mapping[str, Stats]:
    ids_param = ','.join(ids)
    r = await self.client.request(
      'GET', f'{self.base_url.rstrip("/")}/api/v1/latest/{ids_param}',
      headers=self.headers,
    )
    if r.status_code == 404:
      return {}
    raise_on_error(r)
    data = latest_adapter.validate_json(r.text)
    return {
      asset_id: Stats(
        price=values['price_usd'],
        market_cap=values.get('market_cap_usd'),
      )
      for asset_id, values in data.items()
    }

  @SDK.method
  async def historical_price(self, id: str, time: datetime) -> Price | None:
    date = round_date(time)
    date_str = time.strftime('%Y-%m-%d')
    r = await self.client.request(
      'GET', f'{self.base_url.rstrip("/")}/api/v1/historical/{id}',
      headers=self.headers,
      params={'date': date_str},
    )
    if r.status_code == 404:
      return None
    raise_on_error(r)
    data = stats_adapter.validate_json(r.text)
    return Price(price=data['price_usd'], time=date)
