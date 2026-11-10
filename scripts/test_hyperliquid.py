"""The Hyperliquid generator's gates and flag sync, on small offline data."""

import unittest

from hyperliquid import Market, build_report, sync_flags, watch


def market(name, mark, delisted=False, collateral=0):
  dex = name.split(':')[0] if ':' in name else ''
  return Market(name, dex, delisted, mark, '0.0', '0.0', collateral)


def asset(id, symbol, yahoo=None):
  record = {'id': id, 'symbol': symbol}
  if yahoo:
    record['external'] = {'yahoo': yahoo}
  return record


ASSETS = {
  'ciena': asset('ciena', 'CIEN', 'CIEN'),
  'stacks': asset('stacks', 'STX'),
  'seagate-technology': asset('seagate-technology', 'STX', 'STX'),
  'japanese-yen': asset('japanese-yen', 'JPY', 'JPYUSD=X'),
  'solana': asset('solana', 'SOL'),
  'corn': asset('corn', 'CORN'),
  'pear': asset('pear', 'PEAR'),
}
PRICES = {'CIEN': 243.39, 'JPYUSD=X': 0.0063}
COLLATERAL = {'0': 'usd-coin', '360': 'hyperliquid-usd'}


def report(catalogue, venue):
  return build_report(catalogue, venue, ASSETS, COLLATERAL, PRICES.get)


class GatesTest(unittest.TestCase):

  def test_candidate_by_yahoo_price(self):
    venue = {'para:CIEN': market('para:CIEN', 243.94)}
    result = report({}, venue)
    self.assertEqual(result.candidates, {'para:CIEN': {
      'exchange': 'para', 'base': 'ciena', 'quote': 'tether', 'settlement': 'usd-coin',
    }})

  def test_unopened_candidate_is_delisted(self):
    venue = {'km:CIEN': market('km:CIEN', 240.0, delisted=True, collateral=360)}
    candidate = report({}, venue).candidates['km:CIEN']
    self.assertEqual((candidate['settlement'], candidate['delisted']), ('hyperliquid-usd', True))

  def test_candidate_by_listed_hyperliquid_peer(self):
    venue = {'SOL': market('SOL', 150.0), 'flx:SOL': market('flx:SOL', 151.0, collateral=360)}
    catalogue = {'SOL': {'exchange': '', 'base': 'solana', 'quote': 'tether', 'settlement': 'usd-coin'}}
    self.assertEqual(report(catalogue, venue).candidates['flx:SOL']['base'], 'solana')

  def test_shared_symbol_is_unresolved(self):
    result = report({}, {'xyz:STX': market('xyz:STX', 593.0)})
    self.assertIn('symbol shared', result.unresolved['xyz:STX'])

  def test_peer_with_another_base_is_unresolved(self):
    """STX is Stacks on the main dex: a Seagate STX elsewhere is not added by symbol."""
    catalogue = {'STX': {'exchange': '', 'base': 'stacks', 'quote': 'tether', 'settlement': 'usd-coin'}}
    venue = {'STX': market('STX', 0.34), 'xyz:STX': market('xyz:STX', 593.0)}
    assets = {'seagate-technology': ASSETS['seagate-technology']}
    result = build_report(catalogue, venue, assets, COLLATERAL, {'STX': 590.0}.get)
    self.assertIn('STX is stacks', result.unresolved['xyz:STX'])

  def test_price_gap_is_unresolved(self):
    """xyz:JPY prints USD/JPY, not the yen's dollar price."""
    result = report({}, {'xyz:JPY': market('xyz:JPY', 158.2)})
    self.assertIn('beyond', result.unresolved['xyz:JPY'])

  def test_no_reference_or_no_collateral_is_unresolved(self):
    venue = {'xyz:CORN': market('xyz:CORN', 4.6), 'new:CIEN': market('new:CIEN', 243.0, collateral=999)}
    result = report({}, venue)
    self.assertIn('no price reference', result.unresolved['xyz:CORN'])
    self.assertIn('collateral token 999', result.unresolved['new:CIEN'])
    self.assertEqual(result.candidates, {})


class SyncFlagsTest(unittest.TestCase):

  def test_flips_both_ways(self):
    catalogue = {
      'io:NVDA': {'base': 'nvidia', 'delisted': True},
      'TON': {'base': 'toncoin', 'url': 'https://app.hyperliquid.xyz/trade/TON'},
      'BTC': {'base': 'bitcoin'},
      'GONE': {'base': 'gone'},
    }
    venue = {'io:NVDA': market('io:NVDA', 200.0), 'TON': market('TON', 1.0, delisted=True), 'BTC': market('BTC', 1.0)}
    self.assertEqual(sync_flags(catalogue, venue), ['io:NVDA', 'TON'])
    self.assertEqual(catalogue['io:NVDA'], {'base': 'nvidia'})
    self.assertEqual(catalogue['TON'], {'base': 'toncoin', 'delisted': True})
    self.assertEqual(catalogue['GONE'], {'base': 'gone'})


class WatchTest(unittest.TestCase):

  ENTRY = {'QTC/USDC:1188': {
    'coin': '@1188', 'token_id': '0xf5', 'evm_contract': '0xb0', 'circulating_supply': '9000000000.0', 'map_when': 'x',
  }}

  def changes(self, context, circulating='9000000000.0', supply=0):
    contexts = {'@1188': context} if context is not None else {}
    return watch(self.ENTRY, contexts, lambda _: {'circulatingSupply': circulating}, lambda _: supply)['QTC/USDC:1188']

  def test_untraded_unchanged_market(self):
    self.assertEqual(self.changes({'coin': '@1188', 'dayNtlVlm': '0.0', 'markPx': '57.5'}), [])

  def test_each_trigger(self):
    self.assertEqual(len(self.changes({'coin': '@1188', 'dayNtlVlm': '12.5', 'markPx': '0.4'})), 1)
    self.assertEqual(len(self.changes({'coin': '@1188', 'dayNtlVlm': '0.0'}, circulating='21000000.0')), 1)
    self.assertEqual(len(self.changes({'coin': '@1188', 'dayNtlVlm': '0.0'}, supply=10**12)), 1)
    self.assertEqual(len(self.changes(None)), 1)


if __name__ == '__main__':
  unittest.main()
