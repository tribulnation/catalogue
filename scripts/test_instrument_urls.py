"""Regression checks for native instrument IDs versus trading-page IDs."""

import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from instrument_urls import PERPETUAL_RULES, Symbols, fill


class BitgetUrlsTest(unittest.TestCase):
  """Keep UTA links distinct from unverified Classic trading-page routes."""

  def test_product_urls(self):
    """UTA coin pages retain the native suffix exactly once."""
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

  def test_classic_does_not_link_to_uta(self):
    """Missing Classic routes must not silently point at the UTA instrument."""
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    self.assertIsNone(PERPETUAL_RULES['bitget'](
      'BTCUSD', {'exchange': 'coin-classic', 'settlement': 'bitcoin'}, symbols,
    ))

  def test_regeneration_removes_unverified_and_delisted_urls(self):
    """A skipped rule removes a stale URL without dropping the instrument."""
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    rows = {
      'BTCUSD': {'exchange': 'coin-classic', 'settlement': 'bitcoin', 'url': 'wrong'},
      'BTCUSD_CM': {'exchange': 'coin', 'settlement': 'bitcoin'},
      'OLDUSD': {'exchange': 'coin-classic', 'delisted': True, 'url': 'gone'},
    }
    with TemporaryDirectory() as folder:
      path = Path(folder) / 'bitget.json'
      path.write_text(json.dumps(rows))
      result = fill(Path(folder), {'bitget': PERPETUAL_RULES['bitget']}, symbols, overwrite=True)
      updated = json.loads(path.read_text())
    self.assertEqual(result, (1, 1))
    self.assertNotIn('url', updated['BTCUSD'])
    self.assertNotIn('url', updated['OLDUSD'])
    self.assertEqual(updated['BTCUSD_CM']['url'], 'https://www.bitget.com/futures/coin/BTCUSD_CM')


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
