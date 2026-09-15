"""CoinGecko requests full provider precision before parsing current prices."""

from decimal import Decimal
import unittest

from coingecko_sdk import AsyncCoingecko
import httpx

from tribulnation.catalogue.market_data.coingecko import CoingeckoPricing


class CoingeckoRequestPrecisionTest(unittest.IsolatedAsyncioTestCase):
  """Exercise the real SDK HTTP query, including currency reference requests."""

  async def test_market_prices_request_full_precision(self):
    """EURC observations retain all digits because the request asks for them."""
    prices = iter(('1.15914', '1.15328'))
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
      """Model the provider's rounded default response."""
      requests.append(request)
      price = next(prices)
      if request.url.params.get('precision') != 'full':
        price = str(round(Decimal(price), 2))
      return httpx.Response(
        200,
        headers={'content-type': 'application/json'},
        text='[{"id":"euro-coin","current_price":' + price + ',"market_cap":null}]',
      )

    async with AsyncCoingecko(
      demo_api_key='test-only',
      environment='demo',
      http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)),
    ) as client:
      pricing = CoingeckoPricing(client=client, quote='usd')
      before = (await pricing.current_stats(['euro-coin']))['euro-coin'].price
      after = (await pricing.current_stats(['euro-coin']))['euro-coin'].price

    self.assertEqual(before, Decimal('1.15914'))
    self.assertEqual(after, Decimal('1.15328'))
    self.assertEqual(len(requests), 2)
    for request in requests:
      self.assertEqual(request.url.path, '/api/v3/coins/markets')
      self.assertEqual(request.url.params['ids'], 'euro-coin')
      self.assertEqual(request.url.params['vs_currency'], 'usd')
      self.assertEqual(request.url.params['precision'], 'full')

  async def test_both_currency_reference_prices_request_full_precision(self):
    """Derived FX uses full-precision USD and EUR reference observations."""
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
      """Return differently rounded reference prices unless precision is full."""
      requests.append(request)
      currency = request.url.params['vs_currency']
      price = '1.15914' if currency == 'usd' else '0.9999'
      if request.url.params.get('precision') != 'full':
        price = str(round(Decimal(price), 2))
      return httpx.Response(
        200,
        headers={'content-type': 'application/json'},
        text='[{"id":"euro-coin","current_price":' + price + ',"market_cap":null}]',
      )

    async with AsyncCoingecko(
      demo_api_key='test-only',
      environment='demo',
      http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)),
    ) as client:
      pricing = CoingeckoPricing(client=client, quote='usd')
      rate = await pricing.currency_price('eur', reference_asset='euro-coin')

    self.assertEqual(rate, Decimal('1.15914') / Decimal('0.9999'))
    self.assertEqual(len(requests), 2)
    self.assertEqual({r.url.params['vs_currency'] for r in requests}, {'usd', 'eur'})
    for request in requests:
      self.assertEqual(request.url.params['ids'], 'euro-coin')
      self.assertEqual(request.url.params['precision'], 'full')


if __name__ == '__main__':
  unittest.main()
