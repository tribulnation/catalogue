"""`base-quote`, `price` and the external-ID checks, on fixtures from catalogue-ops' issues."""

from pathlib import Path
import unittest

import check_new_assets
from maintenance import base_quote, catalogue, external, observations, runner
from maintenance.catalogue import Catalogue
from maintenance.test_finding import markers

FIXTURES = Path(__file__).with_name('fixtures')


class FixtureTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.catalogue = catalogue.load(FIXTURES / 'data')
    cls.observations = observations.load(FIXTURES / 'observations')
    cls.found = {f['fingerprint']: f for f in runner.run(cls.catalogue, cls.observations, [])['findings']}

  def test_reproduces_published_findings(self):
    for fp in [
      'base-quote:mexc:perp:HK0992_USDT',
      'base-quote:mexc:perp:EWT_USDT',
      'base-quote:bitget:usdt:1000CATUSDT',
      'mismatched-external:catalogue:siren-bsc',
      'mismatched-external:catalogue:intel',
      'mismatched-external:catalogue:applovin',
      'mismatched-external:catalogue:draftkings',
      'dead-external:catalogue:telcoin',
      'missing-external:catalogue:openai',
      'price:coinbase:spot:BLAST-USD',
    ]:
      with self.subTest(fp=fp):
        self.assertIn(fp, markers())
        self.assertIn(fp, self.found)

  def test_price_uses_the_catalogue_quote(self):
    """HK-dollar quanto perps are compared in HK dollars, not USDT (the 683% of #383)."""
    self.assertIn('price:mexc:perp:HK0992_USDT', markers())
    self.assertNotIn('price:mexc:perp:HK0992_USDT', self.found)
    self.assertNotIn('price:binance:usdm:HK0700USDT', self.found)

  def test_disputed_assets_have_no_price_findings(self):
    """Each INTC market would repeat the one `mismatched-external` disagreement."""
    self.assertFalse([fp for fp in self.found if fp.startswith('price:') and 'INTC' in fp])

  def test_mismatched_evidence(self):
    f = self.found['mismatched-external:catalogue:siren-bsc']
    self.assertEqual(f['evidence']['platforms'], ['binance', 'bitget', 'bybit'])
    self.assertAlmostEqual(f['evidence']['implied_usd'], 0.0255, places=3)
    self.assertLessEqual(len(f['evidence']['liquid_markets']), external.EVIDENCE_MARKETS)


class BaseQuoteTest(unittest.TestCase):

  def market(self, **values):
    return observations.parse_listings({'platforms': {'x': {'markets': [
      {'exchange': 'perp', 'market': 'M', 'kind': 'perp', 'status': 'trading', **values},
    ]}}})['x']['markets'][('perp', 'M')]

  def test_index_quote(self):
    instrument = {'kind': 'perp', 'base': 'bitcoin', 'quote': 'tether', 'settlement': 'usd-coin'}
    translations = {'BTC': 'bitcoin', 'USDT': 'tether', 'USDC': 'usd-coin'}
    agree = self.market(base='BTC', quote='USDT', settlement='USDC', index_quote='tether')
    self.assertIsNone(base_quote.compare(instrument, agree, translations))
    differ = self.market(base='BTC', quote='USDT', settlement='USDC', index_quote='usd')
    self.assertEqual(base_quote.compare(instrument, differ, translations)['fields'], ['quote'])

  def test_untranslated_symbols_are_skipped(self):
    instrument = {'kind': 'perp', 'base': 'bitcoin', 'quote': 'tether', 'settlement': 'tether'}
    self.assertIsNone(base_quote.compare(instrument, self.market(base='XBT', quote='USDT'), {'USDT': 'tether'}))

  def test_usdc_quote_rule(self):
    cat = Catalogue(instruments={'lighter': {
      ('perp', 'BTC'): {'kind': 'perp', 'id': 'BTC', 'base': 'bitcoin', 'quote': 'usd-coin', 'settlement': 'usd-coin'},
      ('perp', 'X'): {'kind': 'perp', 'id': 'X', 'base': 'x', 'quote': 'usd-coin', 'settlement': 'usd-coin'},
    }}, assets={'bitcoin': {'category': 'crypto'}})
    found = base_quote.usdc_quotes(cat, {'lighter:X': 'its index is USDC'})
    self.assertEqual([f['fingerprint'] for f in found], ['base-quote:lighter:perp:BTC'])
    self.assertEqual(found[0]['evidence']['usual_quote'], 'tether')


class ExternalTest(unittest.TestCase):

  def test_duplicates(self):
    cat = catalogue.load(FIXTURES / 'data')
    self.assertEqual(
      [f['fingerprint'] for f in external.duplicates(cat)], ['duplicate-external:catalogue:coingecko:blast'],
    )

  def test_dead_needs_a_healthy_source(self):
    cat = catalogue.load(FIXTURES / 'data')
    obs = observations.load(FIXTURES / 'observations')
    obs['prices'] = {**obs['prices'], 'healthy_sources': ['yahoo']}
    self.assertEqual(external.dead(cat, obs, external.traded(cat, obs)), [])

  def test_liquid_assets_need_an_external_id(self):
    errors = check_new_assets.liquid_errors(
      FIXTURES / 'data', {'openai': 5e6, 'bitcoin': 9e9, 'tether': 1e9, 'unknown': 2e5, 'small': 10},
    )
    self.assertEqual([line.split(':')[0] for line in errors], ['openai', 'unknown'])


if __name__ == '__main__':
  unittest.main()
