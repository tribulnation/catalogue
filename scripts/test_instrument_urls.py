"""Regression checks for native instrument IDs versus trading-page IDs."""

import unittest
from pathlib import Path

from instrument_urls import PERPETUAL_RULES, Symbols


class BitgetUrlsTest(unittest.TestCase):
  """Coin API symbols and legacy web symbols resolve to the same page."""

  def test_product_urls(self):
    """Only coin futures need a web-only suffix, added exactly once."""
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    cases = [
      ('BTCUSDT', 'tether', 'usdt/BTCUSDT'),
      ('BTCPERP', 'usd-coin', 'usdc/BTCPERP'),
      ('BTCUSD', 'bitcoin', 'coin/BTCUSD_CM'),
      ('BTCUSD_CM', 'bitcoin', 'coin/BTCUSD_CM'),
    ]
    for id, settlement, path in cases:
      with self.subTest(id=id):
        self.assertEqual(
          PERPETUAL_RULES['bitget'](id, {'settlement': settlement}, symbols),
          f'https://www.bitget.com/futures/{path}',
        )


class CoinbaseUrlsTest(unittest.TestCase):
  """Advanced Trade API IDs retain the separate International Exchange web ID."""

  def test_intx_suffix_is_not_in_the_web_url(self):
    """Native SDK and legacy Catalogue names address the same trading page."""
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    for id in ('BTC-PERP', 'BTC-PERP-INTX'):
      self.assertEqual(
        PERPETUAL_RULES['coinbase'](id, {}, symbols),
        'https://www.coinbase.com/advanced-trade/perpetuals/BTC-PERP',
      )


if __name__ == '__main__':
  unittest.main()
