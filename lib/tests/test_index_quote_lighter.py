"""Lighter quotes follow the currency of each market's oracle sources."""

from pathlib import Path
import unittest

from tribulnation.catalogue.data import load

CATALOGUE = load.all(Path(__file__).resolve().parents[2] / 'data')


class LighterQuoteTest(unittest.TestCase):

  def test_pyth_usd_markets_track_usd(self):
    """Gold, EUR/USD and NVDA take plain Pyth `<BASE>/USD` feeds."""
    for market, base in (('92', 'gold'), ('96', 'euro'), ('110', 'nvidia'), ('145', 'west-texas-intermediate')):
      perp = CATALOGUE.perpetual_for('lighter', market)
      assert perp is not None
      self.assertEqual((perp.base, perp.quote, perp.settlement), (base, 'usd', 'usd-coin'))

  def test_usdt_sourced_crypto_tracks_tether(self):
    """CRO (`73`) takes Chainlink, Pyth and Stork prices divided by USDT."""
    cro = CATALOGUE.perpetual_for('lighter', '73')
    assert cro is not None
    self.assertEqual((cro.quote, cro.settlement), ('tether', 'usd-coin'))

  def test_internal_price_markets_track_usd_or_usdt(self):
    """Markets on Lighter's internal price (pre-IPO, Asian stocks out of hours,
    prelaunch tokens) still track USD (RWA) or USDT (crypto), never their USDC
    settlement: OPENAI, TENCENT (USD-converted HK$ price), XTEN, PRL."""
    for market, quote in (('192', 'usd'), ('201', 'usd'), ('159', 'usd'), ('5628', 'tether'), ('4097', 'tether')):
      perp = CATALOGUE.perpetual_for('lighter', market)
      assert perp is not None
      self.assertEqual((perp.quote, perp.settlement), (quote, 'usd-coin'), market)

  def test_no_lighter_perp_quotes_its_settlement(self):
    """No Lighter perpetual is quoted in USDC (scripts/check_perp_quotes.py)."""
    import json
    data = Path(__file__).resolve().parents[2] / 'data' / 'instruments' / 'perpetual' / 'lighter.json'
    usdc = [id for id, inst in json.loads(data.read_text()).items() if inst['quote'] == 'usd-coin']
    self.assertEqual(usdc, [])

if __name__ == '__main__':
  unittest.main()
