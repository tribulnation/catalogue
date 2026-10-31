"""Ostium perpetuals are quoted in USD, the currency their feeds publish."""

from pathlib import Path
import unittest

from tribulnation.catalogue.data import load

CATALOGUE = load.all(Path(__file__).resolve().parents[2] / 'data')


class OstiumQuoteTest(unittest.TestCase):

  def test_quote_is_usd(self):
    """`<BASE>-USD` markets, FX included, are quoted in USD and settle in USDC."""
    for market, base in (('BTC-USD', 'bitcoin'), ('EUR-USD', 'euro'), ('XAU-USD', 'gold')):
      perp = CATALOGUE.perpetual_for('ostium', market)
      assert perp is not None
      self.assertEqual((perp.base, perp.quote, perp.settlement), (base, 'usd', 'usd-coin'))

  def test_usd_base_pairs_keep_their_quote(self):
    """`USD-JPY` is USD priced in yen."""
    jpy = CATALOGUE.perpetual_for('ostium', 'USD-JPY')
    assert jpy is not None
    self.assertEqual((jpy.base, jpy.quote), ('usd', 'japanese-yen'))


if __name__ == '__main__':
  unittest.main()
