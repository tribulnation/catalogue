"""`untranslated-*`, `stale-listing` and `delisted-live`, on fixtures from catalogue-ops' issues."""

from pathlib import Path
import unittest

from maintenance import catalogue, observations, runner, status, untranslated
from maintenance.catalogue import Catalogue
from maintenance.test_finding import markers

FIXTURES = Path(__file__).with_name('fixtures')


def listings(platform: str, rows: list[dict], *, exchanges=None, complete=True, as_of='2026-11-07T04:50:00Z'):
  return observations.Observations(
    listings=observations.parse_listings(
      {'platforms': {platform: {'complete': complete, 'exchanges': exchanges or {}, 'markets': rows}}}
    ),
    listings_as_of=as_of,
  )


def row(market: str, exchange='perp', kind='perp', **extra):
  return {'exchange': exchange, 'market': market, 'kind': kind, **extra}


class FixtureTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cat = catalogue.load(FIXTURES / 'data')
    obs = observations.load(FIXTURES / 'observations')
    cls.report = runner.run(cat, obs, [])
    cls.found = {f['fingerprint']: f for f in cls.report['findings']}

  def test_reproduces_published_findings(self):
    """Findings catalogue-ops published, rebuilt from the same venue state."""
    for fp in [
      'untranslated-market:hyperliquid:io:io:MU',
      'untranslated-market:dydx:perp:AERO-USD',
      'untranslated-market:mexc:perp:NOCSTOCK_USDT',
      'untranslated-asset:mexc:TSCOSTOCK',
      'stale-listing:kraken:spot:VELODROMEEUR',
      'stale-listing:binance:usdm:CATUSDT',
    ]:
      with self.subTest(fp=fp):
        self.assertIn(fp, markers())
        self.assertIn(fp, self.found)

  def test_drops_published_false_positives(self):
    """A settled dYdX market isn't missing, and a TradFi perp Binance quotes isn't stale."""
    for fp in ['untranslated-market:dydx:perp:ACX-USD', 'stale-listing:binance:usdm:HK0700USDT']:
      with self.subTest(fp=fp):
        self.assertIn(fp, markers())
        self.assertNotIn(fp, self.found)

  def test_sees_what_catalogue_ops_could_not(self):
    """Hyperliquid has no rules surface in catalogue-ops; listing status covers it (#401)."""
    self.assertEqual(self.found['delisted-live:hyperliquid:xyz:xyz:NVDA']['severity'], 'medium')
    self.assertIn('stale-listing:hyperliquid:xyz:xyz:GONE', self.found)
    self.assertNotIn('stale-listing:hyperliquid:xyz:xyz:OLD', self.found)

  def test_pending_markets_are_noted(self):
    market = self.report['checks']['untranslated-market']
    self.assertEqual(market['platforms']['notes'], {'pending_open': {'hyperliquid': ['xyz:xyz:STX']}})
    self.assertNotIn('untranslated-market:hyperliquid:xyz:xyz:STX', self.found)
    self.assertNotIn('untranslated-asset:hyperliquid:STX', self.found)

  def test_incomplete_platform_skips_stale(self):
    self.assertEqual(self.report['checks']['stale-listing']['platforms']['skip'], {'mexc': 'market read incomplete'})


class UntranslatedTest(unittest.TestCase):

  def test_severity_from_volume(self):
    obs = listings('aster', [
      row('AUSDT', base='A', quote='USDT', status='trading', volume_24h_usd=100_000),
      row('BUSDT', base='B', quote='USDT', status='trading', volume_24h_usd=99_999),
      row('CUSDT', base='C', quote='USDT', status='halted', volume_24h_usd=9e9),
    ])
    found, _ = untranslated.markets(Catalogue(), obs)
    self.assertEqual({f['subject']: f['severity'] for f in found}, {'perp:AUSDT': 'medium', 'perp:BUSDT': 'low'})

  def test_assets(self):
    cat = Catalogue(asset_translations={'bybit': {'BONK': 'bonk', 'USDT': 'tether'}}, spam={'bybit': {'0xabc'}})
    obs = listings('bybit', [row('1000BONKUSDT', base='1000BONK', quote='USDT', status='trading')])
    obs['asset_ids'] = {'bybit': {'assets': {'0xABC': ['wallet'], 'DUST': ['wallet'], 'EARNY': ['earn', 'wallet']}}}
    found, coverage = untranslated.assets(cat, obs)
    self.assertEqual({f['subject']: f['severity'] for f in found}, {'DUST': 'low', 'EARNY': 'medium'})
    self.assertEqual(coverage['untranslated-asset']['ran'], ['bybit'])


class StatusTest(unittest.TestCase):

  def instruments(self, **rows):
    return {('perp', id): {'kind': 'perp', 'exchange': 'perp', **row} for id, row in rows.items()}

  def disagreements(self, instruments, rows, as_of='2026-11-07T04:50:00Z'):
    obs = listings('x', rows)
    return {d.key[1]: (d.kind, d.severity) for d in status.disagreements(
      instruments, obs['listings']['x']['markets'], {'perp': 'perp'}, as_of,
    )}

  def test_live_quote_overrides_stale(self):
    found = self.disagreements(self.instruments(A={}, B={}), [
      row('A', status='halted', last_quote_ts='2026-11-07T04:20:00Z'),
      row('B', status='halted', last_quote_ts='2026-11-07T02:00:00Z'),
    ])
    self.assertEqual(found, {'B': ('stale', 'low')})

  def test_zero_volume_is_not_delisted(self):
    """A registered market with no trades yet stays listed (io:NVDA)."""
    found = self.disagreements(self.instruments(A={}, B={'delisted': True}), [
      row('A', status='trading', volume_24h_usd=0, open_interest_usd=0),
      row('B', status='pending'),
    ])
    self.assertEqual(found, {'B': ('delisted-live', 'medium')})

  def test_other_exchanges_are_out_of_scope(self):
    instruments = {('coin-m', 'X'): {'kind': 'perp', 'exchange': 'coin-m'}}
    self.assertEqual(self.disagreements(instruments, []), {})


if __name__ == '__main__':
  unittest.main()
