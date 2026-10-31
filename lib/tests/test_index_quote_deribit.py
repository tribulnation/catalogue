"""Deribit linear perpetuals: BTC and ETH track USD, the rest USDC."""

from pathlib import Path
import unittest

from tribulnation.catalogue.data import load

CATALOGUE = load.all(Path(__file__).resolve().parents[2] / 'data')


class DeribitQuoteTest(unittest.TestCase):

  def test_btc_eth_track_usd(self):
    """The BTC-USDC and ETH-USDC indexes are pegged to BTC-USD and ETH-USD."""
    for market, base in (('BTC_USDC-PERPETUAL', 'bitcoin'), ('ETH_USDC-PERPETUAL', 'ethereum')):
      perp = CATALOGUE.perpetual_for('deribit', market)
      assert perp is not None
      self.assertEqual((perp.base, perp.quote, perp.settlement), (base, 'usd', 'usd-coin'))

  def test_others_track_usdc(self):
    """Other `_usdc` indexes are USD indexes converted at the USDC-USD rate."""
    sol = CATALOGUE.perpetual_for('deribit', 'SOL_USDC-PERPETUAL')
    assert sol is not None
    self.assertEqual((sol.quote, sol.settlement), ('usd-coin', 'usd-coin'))


if __name__ == '__main__':
  unittest.main()
