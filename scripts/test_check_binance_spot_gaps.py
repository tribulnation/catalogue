"""A gap is a trading symbol with both assets translated and no instrument."""

import unittest

from check_binance_spot_gaps import gaps


def market(symbol, base, quote, status='TRADING'):
  return {'symbol': symbol, 'baseAsset': base, 'quoteAsset': quote, 'status': status}


class GapsTest(unittest.TestCase):

  def test_only_translated_trading_missing_symbols(self):
    translations = {'GEVB': 'ge-vernova-bstock', 'SKUUB': 'skuu-bstock', 'USDT': 'tether', 'BTC': 'bitcoin'}
    symbols = [
      market('GEVBUSDT', 'GEVB', 'USDT'),             # gap
      market('SKUUBUSDT', 'SKUUB', 'USDT'),           # gap, larger volume
      market('BTCUSDT', 'BTC', 'USDT'),               # already in the catalogue
      market('NEWUSDT', 'NEW', 'USDT'),               # base not translated
      market('BTCFDUSD', 'BTC', 'FDUSD'),             # quote not translated
      market('OLDBUSDT', 'GEVB', 'USDT', 'BREAK'),    # not trading
    ]
    catalogue = {'BTCUSDT': {}}
    volumes = {'GEVBUSDT': '15893.3', 'SKUUBUSDT': '90000'}
    lines = gaps(symbols, translations, catalogue, volumes)
    self.assertEqual([line.split(':')[0] for line in lines], ['SKUUBUSDT', 'GEVBUSDT'])
    self.assertIn('base ge-vernova-bstock, quote tether', lines[1])

  def test_delisted_instrument_is_not_a_gap(self):
    lines = gaps([market('BTCUSDT', 'BTC', 'USDT')], {'BTC': 'bitcoin', 'USDT': 'tether'}, {'BTCUSDT': {'delisted': True}})
    self.assertEqual(lines, [])


if __name__ == '__main__':
  unittest.main()
