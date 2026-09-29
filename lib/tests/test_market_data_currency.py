"""Market-data adapters never label a local-currency value as the requested quote.

Yahoo and TwelveData payloads below are trimmed from live responses recorded on
2026-09-29 (tribulnation/catalogue#201).
"""

from datetime import datetime
from decimal import Decimal
import unittest

import httpx

from tribulnation.catalogue.market_data.yahoo import YahooPricing, QUOTE_URL, CHART_URL
from tribulnation.catalogue.market_data.twelvedata import TwelveDataPricing

YAHOO_QUOTES = {
  'AAPL': {'currency': 'USD', 'regularMarketPrice': 331.2414, 'marketCap': 4834196455424},
  'EURUSD=X': {'currency': 'USD', 'regularMarketPrice': 1.1336583},
  '2330.TW': {'currency': 'TWD', 'regularMarketPrice': 2475.0, 'marketCap': 64182615539712},
  '2454.TW': {'currency': 'TWD', 'regularMarketPrice': 4910.0, 'marketCap': 7842091761664},
  '6525.T': {'currency': 'JPY', 'regularMarketPrice': 9331.0, 'marketCap': 2177704656896},
  '0992.HK': {'currency': 'HKD', 'regularMarketPrice': 35.48, 'marketCap': 440117297152},
  'VOD.L': {'currency': 'GBp', 'regularMarketPrice': 123.9, 'marketCap': 28633702400},
  'NPN.JO': {'currency': 'ZAc', 'regularMarketPrice': 71483.0, 'marketCap': 534780182528},
  'TEVA.TA': {'currency': 'ILA', 'regularMarketPrice': 11970.0, 'marketCap': 139605229568},
  'NOCCY': {'regularMarketPrice': 10.0},
  'TWDUSD=X': {'currency': 'USD', 'regularMarketPrice': 0.031426776},
  'JPYUSD=X': {'currency': 'USD', 'regularMarketPrice': 0.006347554},
  'HKDUSD=X': {'currency': 'USD', 'regularMarketPrice': 0.12744617},
  'GBPUSD=X': {'currency': 'USD', 'regularMarketPrice': 1.3412},
  'ZARUSD=X': {'currency': 'USD', 'regularMarketPrice': 0.05731},
  'ILSUSD=X': {'currency': 'USD', 'regularMarketPrice': 0.2994},
}

TSMC_CHART = {
  'meta': {'currency': 'TWD', 'exchangeTimezoneName': 'Asia/Taipei', 'gmtoffset': 28800},
  'timestamp': [1790211600],  # 2026-09-24 09:00 Taipei
  'indicators': {'quote': [{'close': [2475.0]}], 'adjclose': [{'adjclose': [2475.0]}]},
}
TWDUSD_CHART = {
  'meta': {'currency': 'USD', 'exchangeTimezoneName': 'Europe/London', 'gmtoffset': 3600},
  'timestamp': [1790204400, 1790290800],  # 2026-09-24 and 09-25 00:00 London (23:00 UTC the day before)
  'indicators': {'quote': [{'close': [0.031456928700208664, 0.031440410763025284]}]},
}
AAPL_CHART = {
  'meta': {'currency': 'USD', 'exchangeTimezoneName': 'America/New_York', 'gmtoffset': -14400},
  'timestamp': [1790256600],  # 2026-09-24 09:30 New York
  'indicators': {'quote': [{'close': [330.5]}], 'adjclose': [{'adjclose': [330.5]}]},
}


class StubHttp:
  """Answer requests from a handler and record each (url, params) pair."""

  def __init__(self, handler):
    self.handler = handler
    self.calls: list[tuple[str, dict]] = []

  async def request(self, method: str, url: str, *, params: dict | None = None, **_):
    """Record the request and return the handler's response."""
    self.calls.append((url, params or {}))
    status, body = self.handler(url, params or {})
    return httpx.Response(status, request=httpx.Request(method, url), json=body)


def yahoo_quotes(quotes: dict[str, dict], *, fail_fx: bool = False):
  """Build a Yahoo quote handler over recorded quotes."""
  def handler(url: str, params: dict):
    assert url == QUOTE_URL, url
    symbols = params['symbols'].split(',')
    if fail_fx and all(s.endswith('=X') for s in symbols):
      return 500, {'finance': {'error': {'description': 'boom'}}}
    result = [{'symbol': s, **quotes[s]} for s in symbols if s in quotes]
    return 200, {'quoteResponse': {'result': result}}
  return handler


def yahoo_charts(charts: dict[str, dict]):
  """Build a Yahoo chart handler over recorded charts."""
  def handler(url: str, _params: dict):
    symbol = url.removeprefix(f'{CHART_URL}/').replace('%3D', '=')
    result = [charts[symbol]] if symbol in charts else []
    return 200, {'chart': {'result': result}}
  return handler


def yahoo(handler) -> tuple[YahooPricing, StubHttp]:
  """Yahoo pricing over a stub client, with the crumb already fetched."""
  http = StubHttp(handler)
  pricing = YahooPricing(quote='USD', client=http)  # type: ignore
  pricing._crumb = 'crumb'
  return pricing, http


class YahooCurrentStatsTest(unittest.IsolatedAsyncioTestCase):
  """`current_stats` returns USD or nothing."""

  async def test_usd_passthrough(self):
    """USD listings keep the provider's exact values and need no FX request."""
    pricing, http = yahoo(yahoo_quotes(YAHOO_QUOTES))
    stats = await pricing.current_stats(['AAPL', 'EURUSD=X'])
    self.assertEqual(stats['AAPL'].price, Decimal('331.2414'))
    self.assertEqual(stats['AAPL'].market_cap, Decimal('4834196455424.00'))
    self.assertEqual(stats['EURUSD=X'].price, Decimal('1.1336583'))
    self.assertEqual(len(http.calls), 1)

  async def test_converts_twd_jpy_hkd(self):
    """Local-currency price and market cap are multiplied by `{CCY}USD=X`, fetched in one batch."""
    pricing, http = yahoo(yahoo_quotes(YAHOO_QUOTES))
    stats = await pricing.current_stats(['AAPL', '2330.TW', '2454.TW', '6525.T', '0992.HK'])
    self.assertEqual(stats['2330.TW'].price, Decimal('2475.0') * Decimal('0.031426776'))
    self.assertEqual(stats['2330.TW'].market_cap, round(Decimal(64182615539712) * Decimal('0.031426776'), 2))
    self.assertEqual(stats['6525.T'].price, Decimal('9331.0') * Decimal('0.006347554'))
    self.assertEqual(stats['0992.HK'].price, Decimal('35.48') * Decimal('0.12744617'))
    self.assertEqual(stats['0992.HK'].market_cap, round(Decimal(440117297152) * Decimal('0.12744617'), 2))
    self.assertEqual(stats['AAPL'].price, Decimal('331.2414'))
    # TSMC is a ~$2T company, not $64T.
    self.assertTrue(Decimal('1.9e12') < stats['2330.TW'].market_cap < Decimal('2.1e12'))  # type: ignore
    self.assertEqual(len(http.calls), 2)
    self.assertEqual(sorted(http.calls[1][1]['symbols'].split(',')), ['HKDUSD=X', 'JPYUSD=X', 'TWDUSD=X'])

  async def test_minor_units(self):
    """Pence, cents and agorot prices are scaled to the major unit; market caps already are."""
    pricing, http = yahoo(yahoo_quotes(YAHOO_QUOTES))
    stats = await pricing.current_stats(['VOD.L', 'NPN.JO', 'TEVA.TA'])
    self.assertEqual(stats['VOD.L'].price, Decimal('123.9') * Decimal('1.3412') / 100)
    self.assertEqual(stats['VOD.L'].market_cap, round(Decimal(28633702400) * Decimal('1.3412'), 2))
    self.assertEqual(stats['NPN.JO'].price, Decimal('71483.0') * Decimal('0.05731') / 100)
    self.assertEqual(stats['NPN.JO'].market_cap, round(Decimal(534780182528) * Decimal('0.05731'), 2))
    self.assertEqual(stats['TEVA.TA'].price, Decimal('11970.0') * Decimal('0.2994') / 100)
    self.assertEqual(sorted(http.calls[1][1]['symbols'].split(',')), ['GBPUSD=X', 'ILSUSD=X', 'ZARUSD=X'])

  async def test_missing_rate_omits_symbol(self):
    """A listing whose FX rate is unavailable is omitted, not returned unconverted."""
    quotes = {k: v for k, v in YAHOO_QUOTES.items() if k != 'JPYUSD=X'}
    pricing, _ = yahoo(yahoo_quotes(quotes))
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      stats = await pricing.current_stats(['AAPL', '2330.TW', '6525.T'])
    self.assertEqual(set(stats), {'AAPL', '2330.TW'})

  async def test_non_usd_rate_omits_symbol(self):
    """An FX quote that is not itself in USD is not used as a USD rate."""
    quotes = {**YAHOO_QUOTES, 'TWDUSD=X': {'currency': 'TWD', 'regularMarketPrice': 1.0}}
    pricing, _ = yahoo(yahoo_quotes(quotes))
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      stats = await pricing.current_stats(['2330.TW'])
    self.assertEqual(stats, {})

  async def test_failed_fx_request_keeps_usd(self):
    """A failed FX request omits the foreign listings and keeps the USD ones."""
    pricing, _ = yahoo(yahoo_quotes(YAHOO_QUOTES, fail_fx=True))
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      stats = await pricing.current_stats(['AAPL', '2330.TW'])
    self.assertEqual(set(stats), {'AAPL'})

  async def test_missing_currency_omits_symbol(self):
    """A quote that does not state its currency is not assumed to be USD."""
    pricing, _ = yahoo(yahoo_quotes(YAHOO_QUOTES))
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      stats = await pricing.current_stats(['AAPL', 'NOCCY'])
    self.assertEqual(set(stats), {'AAPL'})


class YahooHistoricalPriceTest(unittest.IsolatedAsyncioTestCase):
  """`historical_price` returns USD or nothing."""

  async def test_usd_passthrough(self):
    """A USD close is returned as is, with no FX request."""
    pricing, http = yahoo(yahoo_charts({'AAPL': AAPL_CHART}))
    price = await pricing.historical_price('AAPL', datetime(2026, 9, 24))
    self.assertIsNotNone(price)
    self.assertEqual(price.price, Decimal('330.5'))  # type: ignore
    self.assertEqual(len(http.calls), 1)

  async def test_converts_with_same_day_rate(self):
    """A TWD close uses the TWDUSD=X close of the same London date, not the UTC date."""
    pricing, _ = yahoo(yahoo_charts({'2330.TW': TSMC_CHART, 'TWDUSD=X': TWDUSD_CHART}))
    price = await pricing.historical_price('2330.TW', datetime(2026, 9, 24))
    self.assertIsNotNone(price)
    self.assertEqual(price.price, Decimal('2475.0') * Decimal('0.031456928700208664'))  # type: ignore
    self.assertEqual(price.time, datetime(2026, 9, 24))  # type: ignore

  async def test_missing_rate_returns_none(self):
    """Without an FX series the historical price is omitted."""
    pricing, _ = yahoo(yahoo_charts({'2330.TW': TSMC_CHART}))
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      price = await pricing.historical_price('2330.TW', datetime(2026, 9, 24))
    self.assertIsNone(price)


def twelvedata(handler) -> tuple[TwelveDataPricing, StubHttp]:
  """TwelveData pricing over a stub client."""
  http = StubHttp(handler)
  return TwelveDataPricing(quote='USD', params={}, client=http), http  # type: ignore


TD_QUOTES = {
  'AAPL': {'symbol': 'AAPL', 'currency': 'USD', 'close': '331.63'},
  '6525': {'symbol': '6525', 'currency': 'JPY', 'close': '9331'},
  'EUR/USD': {'symbol': 'EUR/USD', 'close': '1.13331'},
}


class TwelveDataCurrencyTest(unittest.IsolatedAsyncioTestCase):
  """TwelveData omits listings that are not in the requested quote."""

  async def test_batch_omits_non_usd(self):
    """A JPY listing is left out of a batch; USD stocks and `*/USD` pairs are kept."""
    pricing, http = twelvedata(lambda url, params: (200, {s: TD_QUOTES[s] for s in params['symbol'].split(',')}))
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      stats = await pricing.current_stats(['AAPL', '6525', 'EUR/USD'])
    self.assertEqual(stats['AAPL'].price, Decimal('331.63'))
    self.assertEqual(stats['EUR/USD'].price, Decimal('1.13331'))
    self.assertNotIn('6525', stats)
    self.assertTrue(http.calls[0][0].endswith('/quote'))

  async def test_single_non_usd(self):
    """A single JPY listing returns nothing."""
    pricing, _ = twelvedata(lambda url, params: (200, TD_QUOTES['6525']))
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      self.assertEqual(await pricing.current_stats(['6525']), {})

  async def test_eur_quote_omits_usd(self):
    """With an EUR quote, USD listings are not relabelled as EUR."""
    http = StubHttp(lambda url, params: (200, TD_QUOTES['AAPL']))
    pricing = TwelveDataPricing(quote='EUR', params={}, client=http)  # type: ignore
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      self.assertEqual(await pricing.current_stats(['AAPL']), {})

  async def test_historical(self):
    """Historical closes are kept for USD series and omitted for JPY ones."""
    def series(currency: str):
      return {'meta': {'currency': currency}, 'values': [{'datetime': '2026-09-24', 'close': '100'}], 'status': 'ok'}
    pricing, _ = twelvedata(lambda url, params: (200, series('USD' if params['symbol'] == 'AAPL' else 'JPY')))
    price = await pricing.historical_price('AAPL', datetime(2026, 9, 24))
    self.assertEqual(price.price, Decimal('100'))  # type: ignore
    with self.assertLogs('tribulnation.catalogue', 'WARNING'):
      self.assertIsNone(await pricing.historical_price('6525', datetime(2026, 9, 24)))


if __name__ == '__main__':
  unittest.main()
