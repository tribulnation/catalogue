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

  def test_unreadable_sources_unchanged(self):
    """Pre-IPO markets on Lighter's internal price keep `usd-coin`."""
    openai = CATALOGUE.perpetual_for('lighter', '192')
    assert openai is not None
    self.assertEqual(openai.quote, 'usd-coin')


if __name__ == '__main__':
  unittest.main()
