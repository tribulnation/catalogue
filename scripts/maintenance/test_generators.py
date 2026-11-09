"""The generators' `--report-json` output, and its merge into a maintenance run."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

import check_binance_spot_gaps
import gtrade
import hyperliquid
from maintenance import catalogue, exceptions, generators, observations, runner
from maintenance.finding import make

FIXTURES = Path(__file__).with_name('fixtures')


def market(name, dex='', delisted=False, volume='0.0', mark=1.0):
  return hyperliquid.Market(name=name, dex=dex, delisted=delisted, mark=mark, open_interest='0.0', volume=volume, collateral=0)


class HyperliquidTest(unittest.TestCase):

  def test_findings(self):
    catalogue_ = {
      'TON': {'exchange': '', 'base': 'ton'},
      'xyz:NVDA': {'exchange': 'xyz', 'base': 'nvidia', 'delisted': True},
      'GONE': {'exchange': ''},
      'OLD': {'exchange': '', 'delisted': True},
    }
    venue = {
      'TON': market('TON', delisted=True),
      'xyz:NVDA': market('xyz:NVDA', dex='xyz'),
      'xyz:MU': market('xyz:MU', dex='xyz', volume='250000.0'),
      'xyz:ODD': market('xyz:ODD', dex='xyz'),
      'xyz:DEAD': market('xyz:DEAD', dex='xyz', delisted=True),
    }
    report = hyperliquid.Report(
      candidates={'xyz:MU': {'exchange': 'xyz', 'base': 'micron', 'quote': 'tether', 'settlement': 'usd-coin'}},
      evidence={'xyz:MU': 'micron: mark 1 vs Yahoo MU 1 (0.0%)'},
      unresolved={'xyz:ODD': 'no match', 'xyz:DEAD': 'no match'},
    )
    found = {f['fingerprint']: f for f in hyperliquid.findings(report, catalogue_, venue)}
    self.assertEqual(sorted(found), [
      'delisted-live:hyperliquid:xyz:xyz:NVDA',
      'stale-listing:hyperliquid::GONE',
      'stale-listing:hyperliquid::TON',
      'untranslated-market:hyperliquid:xyz:xyz:MU',
      'untranslated-market:hyperliquid:xyz:xyz:ODD',
    ])
    self.assertEqual(found['stale-listing:hyperliquid::TON']['evidence']['draft']['set'], {'delisted': True})
    self.assertEqual(found['delisted-live:hyperliquid:xyz:xyz:NVDA']['evidence']['draft']['unset'], ['delisted'])
    self.assertNotIn('draft', found['stale-listing:hyperliquid::GONE']['evidence'])
    mu = found['untranslated-market:hyperliquid:xyz:xyz:MU']
    self.assertEqual((mu['severity'], mu['evidence']['draft']['add']['base']), ('medium', 'micron'))
    self.assertNotIn('draft', found['untranslated-market:hyperliquid:xyz:xyz:ODD']['evidence'])


  def test_hip3_delisted_flag_gets_no_draft(self):
    """On a HIP-3 dex isDelisted also means "not open yet" (#401): report, don't draft."""
    catalogue_ = {'io:NVDA': {'exchange': 'io', 'base': 'nvidia'}, 'TON': {'exchange': '', 'base': 'ton'}}
    venue = {'io:NVDA': market('io:NVDA', dex='io', delisted=True), 'TON': market('TON', delisted=True)}
    found = {f['fingerprint']: f for f in hyperliquid.findings(hyperliquid.Report(), catalogue_, venue)}
    nvda = found['stale-listing:hyperliquid:io:io:NVDA']
    self.assertEqual(nvda['severity'], 'low')
    self.assertNotIn('draft', nvda['evidence'])
    self.assertEqual(found['stale-listing:hyperliquid::TON']['evidence']['draft']['set'], {'delisted': True})


class GtradeTest(unittest.TestCase):

  def test_findings(self):
    old = {
      'a:BTC/USD': {'exchange': 'a', 'base': 'bitcoin', 'quote': 'usd', 'settlement': 'usd-coin'},
      'a:ETH/USD': {'exchange': 'a', 'base': 'ethereum', 'quote': 'usd', 'settlement': 'usd-coin'},
      'a:GONE/USD': {'exchange': 'a', 'base': 'gone', 'quote': 'usd', 'settlement': 'usd-coin'},
    }
    new = {
      'a:BTC/USD': {**old['a:BTC/USD'], 'delisted': True},
      'a:ETH/USD': {**old['a:ETH/USD'], 'quote': 'tether'},
      'a:SOL/USD': {'exchange': 'a', 'base': 'solana', 'quote': 'usd', 'settlement': 'usd-coin'},
    }
    found = {f['fingerprint']: f for f in gtrade.findings(old, new)}
    self.assertEqual(sorted(found), [
      'base-quote:gtrade:a:a:ETH/USD',
      'stale-listing:gtrade:a:a:BTC/USD',
      'stale-listing:gtrade:a:a:GONE/USD',
      'untranslated-market:gtrade:a:a:SOL/USD',
    ])
    self.assertEqual(found['base-quote:gtrade:a:a:ETH/USD']['evidence']['draft']['set'], {'quote': 'tether'})
    self.assertTrue(found['stale-listing:gtrade:a:a:GONE/USD']['evidence']['draft']['remove'])

  def test_committed_file_matches(self):
    """The committed file is the fixture's output, so there is nothing to report."""
    old = json.loads(gtrade.OUTPUT.read_text())
    self.assertEqual(gtrade.findings(old, json.loads(gtrade.render(gtrade.instruments(json.loads(gtrade.FIXTURE.read_text()))))), [])


class BinanceGapsTest(unittest.TestCase):

  def test_findings(self):
    symbols = [
      {'symbol': 'GEVBUSDT', 'status': 'TRADING', 'baseAsset': 'GEVB', 'quoteAsset': 'USDT'},
      {'symbol': 'GEVBBTC', 'status': 'TRADING', 'baseAsset': 'GEVB', 'quoteAsset': 'BTC'},
      {'symbol': 'BTCUSDT', 'status': 'TRADING', 'baseAsset': 'BTC', 'quoteAsset': 'USDT'},
    ]
    translations = {'GEVB': 'ge-vernova-bstock', 'USDT': 'tether', 'BTC': 'bitcoin'}
    found = check_binance_spot_gaps.findings(symbols, translations, {'BTCUSDT': {}}, {'GEVBUSDT': '250000', 'GEVBBTC': '9'})
    self.assertEqual({f['subject']: f['severity'] for f in found}, {'spot:GEVBUSDT': 'medium', 'spot:GEVBBTC': 'low'})
    self.assertEqual(found[0]['evidence']['draft']['add'], {'exchange': 'spot', 'base': 'ge-vernova-bstock', 'quote': 'tether'})


class MergeTest(unittest.TestCase):

  def setUp(self):
    self.catalogue = catalogue.load(FIXTURES / 'data')
    self.observations = observations.load(FIXTURES / 'observations')

  def report(self, findings, checks=('delisted-live', 'stale-listing', 'untranslated-market'), platforms=('hyperliquid',)):
    return {'source': 'scripts/hyperliquid.py', 'platforms': list(platforms), 'checks': list(checks), 'findings': findings}

  def test_merge(self):
    nvda = make('delisted-live', platform='hyperliquid', subject='xyz:xyz:NVDA', severity='medium', summary='',
                evidence={'draft': {'file': 'f', 'id': 'xyz:NVDA', 'unset': ['delisted']}})
    new = make('untranslated-market', platform='hyperliquid', subject='km:km:US500', severity='low', summary='', evidence={})
    report = runner.run(self.catalogue, copy.deepcopy(self.observations), [], extra=[self.report([nvda, new])])
    found = {f['fingerprint']: f for f in report['findings']}
    merged = found['delisted-live:hyperliquid:xyz:xyz:NVDA']['evidence']
    self.assertEqual(merged['draft']['unset'], ['delisted'])
    self.assertEqual(merged['sources'], ['checks', 'scripts/hyperliquid.py'])
    self.assertEqual(found['untranslated-market:hyperliquid:km:km:US500']['evidence']['sources'], ['scripts/hyperliquid.py'])

  def test_extra_covers_and_is_excepted(self):
    without = {k: v for k, v in self.observations.items() if k != 'listings'}
    ewt = make('base-quote', platform='mexc', subject='perp:EWT_USDT', severity='high', summary='', evidence={})
    report = runner.run(self.catalogue, without, exceptions.load(),
                        extra=[self.report([ewt], checks=['base-quote'], platforms=['mexc'])])
    self.assertIn('mexc', report['checks']['base-quote']['platforms']['ran'])
    self.assertIn('base-quote:mexc:perp:EWT_USDT', [f['fingerprint'] for f in report['suppressed']])
    self.assertEqual(report['checks']['stale-listing']['status'], 'skip')

  def test_cli(self):
    import maintain
    with tempfile.TemporaryDirectory() as tmp:
      extra, out = Path(tmp) / 'hl.json', Path(tmp) / 'out.json'
      generators.write(extra, 'scripts/hyperliquid.py', ['hyperliquid'], ['untranslated-market'], [
        make('untranslated-market', platform='hyperliquid', subject='km:km:US500', severity='low', summary='', evidence={}),
      ])
      code = maintain.main([
        '--data', str(FIXTURES / 'data'), '--observations', str(FIXTURES / 'observations'),
        '--extra', str(extra), '--out', str(out),
      ])
      self.assertEqual(code, 0)
      self.assertIn('untranslated-market:hyperliquid:km:km:US500', {f['fingerprint'] for f in json.loads(out.read_text())['findings']})


if __name__ == '__main__':
  unittest.main()
