"""GMX perpetuals are quoted in USD, the currency their oracle prices."""

from pathlib import Path
import unittest

from tribulnation.catalogue.data import load

CATALOGUE = load.all(Path(__file__).resolve().parents[2] / 'data')


class GmxQuoteTest(unittest.TestCase):

  def test_quote_is_usd(self):
    """Every GMX perpetual is quoted in USD and settles in USDC."""
    sol = CATALOGUE.perpetual_for('gmx', 'SOL/USD')
    assert sol is not None
    self.assertEqual((sol.base, sol.quote, sol.settlement), ('solana', 'usd', 'usd-coin'))


if __name__ == '__main__':
  unittest.main()
