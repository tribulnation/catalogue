"""RISEx quotes follow the currency of each market's Stork index feed."""

from pathlib import Path
import unittest

from tribulnation.catalogue.data import load

CATALOGUE = load.all(Path(__file__).resolve().parents[2] / 'data')


class RisexQuoteTest(unittest.TestCase):

  def test_crypto_markets_track_usdc(self):
    """Crypto markets take Stork `<BASE>USDC` feeds and are documented as USDC-priced."""
    for market, base in (('1', 'bitcoin'), ('2', 'ethereum'), ('54', 'pepe')):
      perp = CATALOGUE.perpetual_for('risex', market)
      assert perp is not None
      self.assertEqual((perp.base, perp.quote, perp.settlement), (base, 'usd-coin', 'usd-coin'))

  def test_rwa_markets_track_usdt(self):
    """RWA markets take Stork `<BASE>USDT_IDX_BIF` feeds and are documented as USDT-priced."""
    for market, base in (('17', 'gold'), ('19', 'west-texas-intermediate'), ('36', 'nvidia')):
      perp = CATALOGUE.perpetual_for('risex', market)
      assert perp is not None
      self.assertEqual((perp.base, perp.quote, perp.settlement), (base, 'tether', 'usd-coin'))


if __name__ == '__main__':
  unittest.main()
