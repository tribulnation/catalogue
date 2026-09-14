"""Regression checks that market-data adapters keep provider price precision."""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
import unittest

import httpx

from tribulnation.catalogue.market_data.util import parse_price
from tribulnation.catalogue.market_data.coinmarketcap import CoinMarketCapPricing
from tribulnation.catalogue.market_data.fred import FredPricing

try:
  from tribulnation.catalogue.market_data.coingecko import CoingeckoPricing
except ModuleNotFoundError:
  CoingeckoPricing = None

EURC_BEFORE = 1.15914
"""Full-precision EURC/USD observation that used to be stored as 1.16."""
EURC_AFTER = 1.15328
"""Next observation, which used to be stored as 1.15."""
EURC_MOVE = Decimal('-0.00586')

class StubHttp:
  """Answer every request with one canned response."""

  def __init__(self, **kwargs):
    self.kwargs = kwargs

  async def request(self, method: str, url: str, **_):
    """Return the canned response for any request."""
    return httpx.Response(200, request=httpx.Request(method, url), **self.kwargs)

class ParsePriceTest(unittest.TestCase):
  """Provider values convert to `Decimal` exactly, without rounding."""

  def test_eurc_sized_floats(self):
    """Float prices keep their digits and no binary noise."""
    self.assertEqual(parse_price(EURC_BEFORE), Decimal('1.15914'))
    self.assertEqual(parse_price(EURC_AFTER) - parse_price(EURC_BEFORE), EURC_MOVE)

  def test_strings_and_decimals(self):
    """String and `Decimal` inputs pass through unchanged."""
    self.assertEqual(parse_price('1.15914'), Decimal('1.15914'))
    self.assertEqual(parse_price(Decimal('0.000012345678')), Decimal('0.000012345678'))

class AdapterPrecisionTest(unittest.IsolatedAsyncioTestCase):
  """Adapters return prices exactly as the provider reported them."""

  @unittest.skipIf(CoingeckoPricing is None, 'coingecko-sdk not installed')
  async def test_coingecko_markets(self):
    """CoinGecko floats survive `current_stats` without rounding to cents."""
    prices = iter([EURC_BEFORE, EURC_AFTER])
    async def get(**_):
      return [SimpleNamespace(id='euro-coin', current_price=next(prices), market_cap=None)]
    client = SimpleNamespace(coins=SimpleNamespace(markets=SimpleNamespace(get=get)))
    pricing = CoingeckoPricing(client=client, quote='usd') # type: ignore
    before = (await pricing.current_stats(['euro-coin']))['euro-coin'].price
    after = (await pricing.current_stats(['euro-coin']))['euro-coin'].price
    self.assertEqual(before, Decimal('1.15914'))
    self.assertEqual(after, Decimal('1.15328'))
    self.assertEqual(after - before, EURC_MOVE) # type: ignore

  async def test_coinmarketcap_quotes(self):
    """CoinMarketCap JSON prices survive `current_stats` without rounding to cents."""
    body = {'data': {'20641': {'id': 20641, 'quote': {'USD': {'price': EURC_BEFORE}}}}}
    pricing = CoinMarketCapPricing(quote='usd', headers={}, client=StubHttp(json=body)) # type: ignore
    stats = await pricing.current_stats(['20641'])
    self.assertEqual(stats['20641'].price, Decimal('1.15914'))

  async def test_fred_observations(self):
    """FRED CSV observations keep every published digit."""
    csv = 'observation_date,DEXUSEU\n2026-09-10,1.1591\n2026-09-11,1.1533\n'
    pricing = FredPricing(quote='USD', client=StubHttp(text=csv)) # type: ignore
    price = await pricing.historical_price('DEXUSEU', datetime(2026, 9, 11))
    self.assertIsNotNone(price)
    self.assertEqual(price.price, Decimal('1.1533')) # type: ignore

if __name__ == '__main__':
  unittest.main()
