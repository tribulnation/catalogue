"""Derive perpetuals are quoted in USD, the currency their index tracks."""

from pathlib import Path
import unittest

from tribulnation.catalogue.data import load

CATALOGUE = load.all(Path(__file__).resolve().parents[2] / 'data')


class DeriveQuoteTest(unittest.TestCase):

  def test_quote_is_usd(self):
    """`BTC-PERP` is quoted in USD and settles in USDC."""
    perp = CATALOGUE.perpetual_for('derive', 'BTC-PERP')
    assert perp is not None
    self.assertEqual((perp.base, perp.quote, perp.settlement), ('bitcoin', 'usd', 'usd-coin'))


if __name__ == '__main__':
  unittest.main()
