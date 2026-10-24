"""ISO 4217 external IDs: validation, forward-compatible loading and ECB reference rates."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
import io
import json
import unittest
import zipfile

import httpx
from pydantic import ValidationError

from tribulnation.catalogue.data import load, validate
from tribulnation.catalogue.market_data.ecb import EcbPricing, DAILY_URL, DATA_URL

DATA = Path(__file__).resolve().parents[2] / 'data'
CATALOGUE = load.all(DATA)

ECB_DAILY = """<?xml version="1.0" encoding="UTF-8"?>
<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01" xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
  <gesmes:subject>Reference rates</gesmes:subject>
  <Cube>
    <Cube time='2026-10-23'>
      <Cube currency='USD' rate='1.1193'/>
      <Cube currency='JPY' rate='175.51'/>
      <Cube currency='CHF' rate='0.9227'/>
    </Cube>
  </Cube>
</gesmes:Envelope>"""
"""Trimmed from the ECB daily feed of 2026-10-23."""

ECB_CSV = """KEY,FREQ,CURRENCY,CURRENCY_DENOM,EXR_TYPE,EXR_SUFFIX,TIME_PERIOD,OBS_VALUE
EXR.D.JPY.EUR.SP00.A,D,JPY,EUR,SP00,A,2026-10-22,175.97
EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-10-22,1.1205
"""
"""Trimmed from the ECB Data Portal `EXR` CSV of 2026-10-22."""


class StubHttp:
  """Answer requests by URL prefix and record each (url, params) pair."""

  def __init__(self, bodies: dict[str, str]):
    self.bodies = bodies
    self.calls: list[tuple[str, dict | None]] = []

  async def request(self, method: str, url: str, *, params: dict | None = None, **_):
    """Return the body registered for the URL's prefix."""
    self.calls.append((url, params))
    body = next(b for prefix, b in self.bodies.items() if url.startswith(prefix))
    return httpx.Response(200, request=httpx.Request(method, url), text=body)


def asset(id: str, symbol: str, category: str | None, code: str | None) -> dict:
  return {
    'id': id, 'display_name': id, 'symbol': symbol, 'category': category,
    'external': {'iso4217': code} if code else {},
  }


class ValidateTest(unittest.TestCase):
  """`validate.iso4217_codes` keeps codes to fiat and precious metals, one asset each."""

  def test_shipped_data(self):
    """The shipped assets validate and every ECB reference currency has its code."""
    self.assertEqual(validate.iso4217_codes(CATALOGUE.assets), [])
    codes = {code for a in CATALOGUE.assets.values() if (code := a.get('external', {}).get('iso4217'))}
    ecb = set('USD JPY CZK DKK GBP HUF PLN RON SEK CHF ISK NOK TRY AUD BRL CAD CNY HKD IDR ILS INR KRW MXN MYR NZD PHP SGD THB ZAR'.split())
    self.assertLessEqual(ecb | {'EUR', 'XAU', 'XAG', 'XPT', 'XPD'}, codes)

  def test_rejects(self):
    """Malformed, misplaced, mismatched, missing and duplicated codes are reported."""
    cases = {
      'malformed': {'a': asset('a', 'usd', 'fiat', 'usd')},
      'crypto': {'bitcoin': asset('bitcoin', 'XBT', 'crypto', 'XBT')},
      'non-iso commodity': {'copper': asset('copper', 'XCU', 'commodity', 'XCU')},
      'stablecoin': {'usdc': asset('usdc', 'USD', 'stablecoin', 'USD')},
      'symbol mismatch': {'usd': asset('usd', 'USDX', 'fiat', 'USD')},
      'missing': {'usd': asset('usd', 'USD', 'fiat', None)},
      'duplicate': {'usd': asset('usd', 'USD', 'fiat', 'USD'), 'usd-2': asset('usd-2', 'USD', 'fiat', 'USD')},
    }
    for name, assets in cases.items():
      with self.subTest(name):
        self.assertEqual(len(validate.iso4217_codes(assets)), 1) # type: ignore

  def test_accepts_metals(self):
    """Gold carries its ISO 4217 code."""
    self.assertEqual(validate.iso4217_codes({'gold': asset('gold', 'XAU', 'commodity', 'XAU')}), []) # type: ignore


class LoadTest(unittest.TestCase):
  """Unknown external providers in newer live data do not cost the asset."""

  def archive(self) -> bytes:
    usd = asset('usd', 'USD', 'fiat', 'USD')
    usd['external']['some-future-provider'] = 'x'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
      zf.writestr('assets/usd.json', json.dumps(usd))
      zf.writestr('platforms/order.txt', '')
    return buf.getvalue()

  def test_lenient_load_drops_unknown_provider(self):
    """Outside strict mode the asset loads with its known external IDs."""
    catalogue = load.archive(self.archive(), skip_invalid=True)
    self.assertEqual(catalogue.assets['usd'].get('external'), {'iso4217': 'USD'})

  def test_strict_load_rejects_unknown_provider(self):
    """Strict mode (used by `scripts/validate.py`) still rejects a typo'd provider."""
    with self.assertRaises(ValidationError):
      load.archive(self.archive(), strict=True)


class EcbPricingTest(unittest.IsolatedAsyncioTestCase):
  """ECB rates (currency per EUR) become prices in the requested quote."""

  async def test_current_usd(self):
    """Current prices cross through EUR; USD is 1 and unpublished codes are absent."""
    http = StubHttp({DAILY_URL: ECB_DAILY})
    stats = await EcbPricing(quote='USD', client=http).current_stats(['EUR', 'JPY', 'USD', 'XAU']) # type: ignore
    self.assertEqual(set(stats), {'EUR', 'JPY', 'USD'})
    self.assertEqual(stats['EUR'].price, Decimal('1.1193'))
    self.assertEqual(stats['USD'].price, Decimal(1))
    self.assertEqual(stats['JPY'].price, Decimal('1.1193') / Decimal('175.51'))

  async def test_current_eur(self):
    """EUR quotes invert the published rate."""
    http = StubHttp({DAILY_URL: ECB_DAILY})
    stats = await EcbPricing(quote='EUR', client=http).current_stats(['CHF', 'EUR']) # type: ignore
    self.assertEqual(stats['CHF'].price, Decimal(1) / Decimal('0.9227'))
    self.assertEqual(stats['EUR'].price, Decimal(1))

  async def test_historical(self):
    """Historical prices use that day's series for the asset and the quote."""
    http = StubHttp({DATA_URL: ECB_CSV})
    price = await EcbPricing(quote='USD', client=http).historical_price('JPY', datetime(2026, 10, 22, 15)) # type: ignore
    self.assertEqual(price.price, Decimal('1.1205') / Decimal('175.97')) # type: ignore
    self.assertEqual(price.time, datetime(2026, 10, 22)) # type: ignore
    url, params = http.calls[0]
    self.assertEqual(url, f'{DATA_URL}/D.JPY+USD.EUR.SP00.A')
    self.assertEqual(params, {'startPeriod': '2026-10-22', 'endPeriod': '2026-10-22', 'format': 'csvdata'})

  async def test_no_observation(self):
    """Weekends and holidays have no reference rate and are not forward-filled."""
    http = StubHttp({DATA_URL: ''})
    self.assertIsNone(await EcbPricing(quote='USD', client=http).historical_price('JPY', datetime(2026, 10, 24))) # type: ignore

  async def test_invalid_code(self):
    """IDs must be ISO 4217 codes, so nothing else reaches the series key."""
    from tribulnation.sdk import ApiError
    with self.assertRaises(ApiError):
      await EcbPricing(quote='USD', client=StubHttp({})).historical_price('jpy+USD', datetime(2026, 10, 22)) # type: ignore


if __name__ == '__main__':
  unittest.main()
