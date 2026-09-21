"""Offline HTTP fixtures for DefiLlama prices, timestamps and quote conversion."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

import httpx
from tribulnation.sdk import ApiError

from tribulnation.catalogue.api.schema.assets import ExternalIds
from tribulnation.catalogue.market_data import DefiLlamaPricing, Pricing

TOKEN = 'polygon:0x12050c705152931cfee3dd56c52fb09dea816c23'
OBSERVED = datetime(2026, 9, 19, 10, 30, tzinfo=timezone.utc)
FX = 'observation_date,DEXUSEU\n2026-09-17,1.1\n2026-09-18,1.25\n2026-09-21,1.5\n'


class FixtureHttp:
  """Return canned token-price JSON and FRED CSV while recording requests."""

  def __init__(self, coins: dict, *, fx: str = FX):
    """Store fixture bodies and an initially empty request log."""
    self.coins = coins
    self.fx = fx
    self.requests: list[httpx.Request] = []

  async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
    """Respond by host so token and FX requests are independently checked."""
    request = httpx.Request(method, url, params=kwargs.get('params'))
    self.requests.append(request)
    if request.url.host == 'fred.stlouisfed.org':
      return httpx.Response(200, request=request, text=self.fx)
    return httpx.Response(200, request=request, json={'coins': self.coins})


def pricing(coins: dict, *, quote='usd', fx=FX) -> tuple[DefiLlamaPricing, FixtureHttp]:
  """Construct a pricing adapter backed entirely by HTTP fixtures."""
  client = FixtureHttp(coins, fx=fx)
  return DefiLlamaPricing(quote=quote, client=client), client  # type: ignore


class DefiLlamaPricingTests(unittest.IsolatedAsyncioTestCase):
  """Validate user-visible pricing behavior without live network calls."""

  async def test_usd_precision_zero_missing_and_unrequested(self):
    """Keep full Decimal precision and zero while excluding omitted values."""
    sdk, client = pricing(
      {
        TOKEN: {'price': '0.000315894971930910612345'},
        'coingecko:zero': {'price': 0},
        'coingecko:null': {'price': None},
        'coingecko:empty': {},
        'unrequested': {'price': 42},
      }
    )
    stats = await sdk.current_stats(
      [
        TOKEN,
        'coingecko:zero',
        'coingecko:null',
        'coingecko:empty',
        'coingecko:missing',
      ]
    )
    self.assertEqual(set(stats), {TOKEN, 'coingecko:zero'})
    self.assertEqual(stats[TOKEN].price, Decimal('0.000315894971930910612345'))
    self.assertEqual(stats['coingecko:zero'].price, Decimal(0))
    self.assertIsNone(stats[TOKEN].market_cap)
    self.assertEqual(len(client.requests), 1)
    self.assertIn('/prices/current/polygon:', client.requests[0].url.path)

  async def test_numeric_json_keeps_all_provider_digits(self):
    """Numeric JSON must not pass through binary float before Decimal parsing."""
    body = '{"coins":{"polygon:token":{"price":0.000315894971930910612345}}}'

    async def response(request: httpx.Request) -> httpx.Response:
      """Return literal JSON so the fixture cannot round its numeric token."""
      return httpx.Response(200, request=request, content=body)

    async with httpx.AsyncClient(transport=httpx.MockTransport(response)) as client:
      sdk = DefiLlamaPricing(client=client)  # type: ignore
      stats = await sdk.current_stats(['polygon:token'])
    self.assertEqual(
      stats['polygon:token'].price, Decimal('0.000315894971930910612345')
    )

  async def test_empty_input_does_not_fetch(self):
    """An empty batch requires no price or FX requests."""
    sdk, client = pricing({}, quote='eur')
    self.assertEqual(await sdk.current_stats([]), {})
    self.assertEqual(client.requests, [])

  async def test_historical_uses_requested_instant_and_returned_timestamp(self):
    """Use UTC epoch seconds, returning the actual provider observation time."""
    sdk, client = pricing(
      {TOKEN: {'price': 0.0003158, 'timestamp': int(OBSERVED.timestamp())}}
    )
    target = datetime(2026, 9, 19, 13, tzinfo=timezone(timedelta(hours=2)))
    result = await sdk.historical_price(TOKEN, target)
    self.assertIsNotNone(result)
    self.assertEqual(result.price, Decimal('0.0003158'))  # type: ignore
    self.assertEqual(result.time, OBSERVED)  # type: ignore
    self.assertIn(
      f'/historical/{int(target.timestamp())}/', client.requests[0].url.path
    )

  async def test_naive_request_is_utc(self):
    """Naive request times have deterministic UTC semantics."""
    sdk, client = pricing({})
    self.assertIsNone(await sdk.historical_price(TOKEN, OBSERVED.replace(tzinfo=None)))
    self.assertIn(
      f'/historical/{int(OBSERVED.timestamp())}/', client.requests[0].url.path
    )

  async def test_historical_omissions(self):
    """Missing price or observation time must not produce an invented quote."""
    for coin in [{}, {'price': 1}, {'timestamp': 10}, {'price': None, 'timestamp': 10}]:
      with self.subTest(coin=coin):
        sdk, _ = pricing({TOKEN: coin})
        self.assertIsNone(await sdk.historical_price(TOKEN, OBSERVED))

  async def test_eur_current_uses_observation_date_fx(self):
    """Divide USD by USD-per-EUR, carrying Friday's rate across a weekend."""
    sdk, client = pricing(
      {TOKEN: {'price': 2.5, 'timestamp': int(OBSERVED.timestamp())}}, quote='eur'
    )
    self.assertEqual((await sdk.current_stats([TOKEN]))[TOKEN].price, Decimal('2'))
    self.assertEqual(client.requests[1].url.params['id'], 'DEXUSEU')

  async def test_eur_history_does_not_use_future_fx(self):
    """Historical conversion uses the observation date, not a later target date."""
    sdk, _ = pricing(
      {TOKEN: {'price': 2.5, 'timestamp': int(OBSERVED.timestamp())}}, quote='eur'
    )
    result = await sdk.historical_price(TOKEN, OBSERVED + timedelta(days=3))
    self.assertIsNotNone(result)
    self.assertEqual(result.price, Decimal('2'))  # type: ignore
    self.assertEqual(result.time, OBSERVED)  # type: ignore

  async def test_missing_fx_never_returns_usd_as_eur(self):
    """Unavailable or future-only FX yields no converted price."""
    for fx in [
      'observation_date,DEXUSEU\n',
      'observation_date,DEXUSEU\n2026-09-21,1.5\n',
    ]:
      with self.subTest(fx=fx):
        sdk, _ = pricing(
          {TOKEN: {'price': 2.5, 'timestamp': int(OBSERVED.timestamp())}},
          quote='eur',
          fx=fx,
        )
        self.assertEqual(await sdk.current_stats([TOKEN]), {})
        self.assertIsNone(await sdk.historical_price(TOKEN, OBSERVED))
    sdk, _ = pricing({TOKEN: {'price': 2.5}}, quote='eur')
    self.assertEqual(await sdk.current_stats([TOKEN]), {})

  async def test_invalid_price_and_fx_are_api_errors(self):
    """Reject negative prices and zero conversion rates rather than misprice."""
    sdk, _ = pricing({TOKEN: {'price': -1}})
    with self.assertRaises(ApiError):
      await sdk.current_stats([TOKEN])
    sdk, _ = pricing(
      {TOKEN: {'price': 1, 'timestamp': int(OBSERVED.timestamp())}},
      quote='eur',
      fx='observation_date,DEXUSEU\n2026-09-18,0\n',
    )
    with self.assertRaises(ApiError):
      await sdk.current_stats([TOKEN])

  async def test_public_factory_and_external_schema(self):
    """The source factory, lazy export and API schema recognize DefiLlama."""
    sdk = Pricing.of('defillama', quote='eur')
    self.assertIsInstance(sdk, DefiLlamaPricing)
    self.assertEqual(sdk.quote, 'eur')
    self.assertEqual(ExternalIds(defillama=TOKEN).defillama, TOKEN)
    with self.assertRaises(ValueError):
      DefiLlamaPricing.new(quote='gbp')  # type: ignore


if __name__ == '__main__':
  unittest.main()
