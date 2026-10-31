"""Pacifica crypto perpetuals are quoted in USDT, the currency of their oracle."""

from pathlib import Path
import unittest

from tribulnation.catalogue.data import load

CATALOGUE = load.all(Path(__file__).resolve().parents[2] / 'data')


class PacificaQuoteTest(unittest.TestCase):

  def test_crypto_tracks_tether(self):
    """The oracle is a weighted average of USDT prices; settlement stays USDC."""
    btc = CATALOGUE.perpetual_for('pacifica', 'BTC')
    assert btc is not None
    self.assertEqual((btc.base, btc.quote, btc.settlement), ('bitcoin', 'tether', 'usd-coin'))

  def test_rwa_unchanged(self):
    """Stock markets keep `usd-coin` until their index is defined."""
    tsla = CATALOGUE.perpetual_for('pacifica', 'TSLA')
    assert tsla is not None
    self.assertEqual(tsla.quote, 'usd-coin')


if __name__ == '__main__':
  unittest.main()
