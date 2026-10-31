"""Extended order-book perpetuals are quoted in USD; RFQ markets are unchanged."""

from pathlib import Path
import unittest

from tribulnation.catalogue.data import load

CATALOGUE = load.all(Path(__file__).resolve().parents[2] / 'data')


class ExtendedQuoteTest(unittest.TestCase):

  def test_order_book_markets_track_usd(self):
    """Stork's crypto prices and the RWA references are USD-denominated."""
    for market, base in (('BTC-USD', 'bitcoin'), ('EUR-USD', 'euro'), ('XAU-USD', 'gold')):
      perp = CATALOGUE.perpetual_for('extended', market)
      assert perp is not None
      self.assertEqual((perp.base, perp.quote, perp.settlement), (base, 'usd', 'usd-coin'))

  def test_rfq_markets_unchanged(self):
    """An RFQ market keeps `usd-coin`."""
    pepe = CATALOGUE.perpetual_for('extended', '1000PEPE-USD')
    assert pepe is not None
    self.assertEqual(pepe.quote, 'usd-coin')


if __name__ == '__main__':
  unittest.main()
