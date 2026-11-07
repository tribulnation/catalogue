"""The delisted comparison follows `isDelisted`, not open interest or volume."""

import unittest

from check_hyperliquid_delisted import disagreements


class DisagreementsTest(unittest.TestCase):

  def test_unopened_market_is_not_delisted(self):
    """A registered market with no trades yet stays listed."""
    venue = {'io:NVDA': {'delisted': False, 'open_interest': '0.0', 'volume': '0.0'}}
    self.assertEqual(disagreements({'io:NVDA': {}}, venue), [])
    self.assertEqual(len(disagreements({'io:NVDA': {'delisted': True}}, venue)), 1)

  def test_both_directions(self):
    venue = {
      'TON': {'delisted': True, 'open_interest': '0.0', 'volume': '0.0'},
      'BTC': {'delisted': False, 'open_interest': '1', 'volume': '1'},
    }
    catalogue = {'TON': {}, 'BTC': {'delisted': True}, 'GONE': {}, 'OLD': {'delisted': True}}
    lines = disagreements(catalogue, venue)
    self.assertEqual([line.split(':')[0] for line in lines], ['TON', 'BTC', 'GONE'])


if __name__ == '__main__':
  unittest.main()
