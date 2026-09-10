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
  """Advanced Trade pages require the full native product ID."""

  def test_intx_suffix_is_preserved_in_the_web_url(self):
    """The web route must not strip the product's International Exchange suffix."""
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    for id in ('BTC-PERP-INTX', 'ETH-PERP-INTX', '1000BONK-PERP-INTX'):
      self.assertEqual(
        PERPETUAL_RULES['coinbase'](id, {}, symbols),
        f'https://www.coinbase.com/advanced-trade/perpetuals/{id}',
      )


if __name__ == '__main__':
  unittest.main()
