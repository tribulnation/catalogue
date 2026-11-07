"""The findings catalogue-ops kept reporting and its fixer kept dismissing, each from the
issue's own evidence: fixed in the check where the check was wrong, excepted where only
a schema decision can settle it."""

import copy
from pathlib import Path
import unittest

from maintenance import base_quote, catalogue, exceptions, external, observations, runner, sessions
from maintenance.observations import timestamp
from maintenance.test_finding import markers

FIXTURES = Path(__file__).with_name('fixtures')
CATALOGUE = catalogue.load(FIXTURES / 'data')
OBSERVATIONS = observations.load(FIXTURES / 'observations')


def run(obs=OBSERVATIONS, entries=None):
  report = runner.run(CATALOGUE, obs, exceptions.load() if entries is None else entries)
  return report, {f['fingerprint'] for f in report['findings']}, {f['fingerprint'] for f in report['suppressed']}


def market(**values):
  row = {'exchange': 'perp', 'market': 'M', 'kind': 'perp', 'status': 'trading', **values}
  return observations.parse_listings({'platforms': {'x': {'markets': [row]}}})['x']['markets'][('perp', 'M')]


class QuantoTest(unittest.TestCase):
  """MEXC HK0700/HK1810/HK0992: HK-dollar prices, USDT margin (#382, #383, #387)."""

  translations = {'HK0700': 'tencent-holdings', 'USDT': 'tether', 'USDC': 'usd-coin', 'BTC': 'bitcoin'}
  hk0700 = {'kind': 'perp', 'base': 'tencent-holdings', 'quote': 'hong-kong-dollar', 'settlement': 'tether', 'quanto': True}

  def test_quanto_quote_label_is_the_settlement(self):
    """Issue #387 finding 5: venue `quoteCoin: USDT`, catalogue hong-kong-dollar/tether."""
    venue = market(base='HK0700', quote='USDT', settlement='USDT')
    self.assertIsNone(base_quote.compare(self.hk0700, venue, self.translations, 'mexc'))
    self.assertIsNone(base_quote.compare({**self.hk0700, 'quanto': False}, venue, self.translations, 'mexc'))

  def test_published_quanto_findings_are_gone(self):
    _, found, _ = run()
    self.assertIn('base-quote:mexc:perp:HK0992_USDT', markers())
    self.assertNotIn('base-quote:mexc:perp:HK0992_USDT', found)
    self.assertNotIn('price:mexc:perp:HK0992_USDT', found)

  def test_a_wrong_quote_still_fires(self):
    """Without `quanto`, and with quote equal to settlement, the venue's label is compared as before."""
    plain = {'kind': 'perp', 'base': 'tencent-holdings', 'quote': 'hong-kong-dollar', 'settlement': 'tether'}
    venue = market(base='HK0700', quote='USDT', settlement='USDT')
    self.assertEqual(base_quote.compare(plain, venue, self.translations, 'mexc')['fields'], ['quote'])
    usdc = market(base='HK0700', quote='USDC', settlement='USDT')
    self.assertEqual(base_quote.compare(self.hk0700, usdc, self.translations, 'mexc')['fields'], ['quote'])

  def test_hyperliquid_labels_the_settlement(self):
    """Hyperliquid labels BTC with USDC; its index is USDT, as the catalogue says."""
    btc = {'kind': 'perp', 'base': 'bitcoin', 'quote': 'tether', 'settlement': 'usd-coin'}
    venue = market(base='BTC', quote='USDC', settlement='USDC')
    self.assertIsNone(base_quote.compare(btc, venue, self.translations, 'hyperliquid'))
    self.assertIsNotNone(base_quote.compare(btc, venue, self.translations, 'binance'))
    usd_index = market(base='BTC', quote='USDC', settlement='USDC', index_quote='usd')
    self.assertEqual(base_quote.compare(btc, usd_index, self.translations, 'hyperliquid')['fields'], ['quote'])


class ClosingReferenceTest(unittest.TestCase):
  """intel/INTW (#360/#361), applovin (#391/#392), draftkings (#393/#395): a previous
  close against perps that already priced the news."""

  def obs(self, as_of, quote_usd, quote_as_of):
    obs = copy.deepcopy(OBSERVATIONS)
    obs['listings_as_of'] = as_of
    obs['prices']['assets']['intel'] = {'providers': {'yahoo': {'usd': quote_usd, 'as_of': quote_as_of}}}
    return obs

  def test_published_findings_are_gone(self):
    report, found, _ = run()
    for asset in ('intel', 'applovin', 'draftkings'):
      with self.subTest(asset=asset):
        self.assertIn(f'mismatched-external:catalogue:{asset}', markers())
        self.assertNotIn(f'mismatched-external:catalogue:{asset}', found)
        self.assertIn(asset, report['checks']['mismatched-external']['platforms']['notes']['closing_reference'])
    self.assertFalse([fp for fp in found if fp.startswith('price:') and ('INTC' in fp or 'DKNG' in fp or 'APP' in fp)])

  def test_intel_crash_morning(self):
    """#360: read 04:39 UTC on 2026-10-30, against the 10-29 close of 92.07."""
    obs = self.obs('2026-10-30T04:39:00Z', 92.07, '2026-10-29T20:00:00Z')
    self.assertEqual(
      sessions.closing_reference(CATALOGUE, obs, 'intel', obs['prices']['assets']['intel']['providers']),
      'outside the listing session',
    )

  def test_in_session_a_wrong_id_still_fires(self):
    """At 15:00 UTC on a Monday with a fresh quote, a 22% gap is a real disagreement."""
    history = [{'ts': '2026-11-09T14:30:00Z', 'implied_usd': 71.6, 'reference_usd': 92.0}]
    obs = self.obs('2026-11-09T15:00:00Z', 92.07, '2026-11-09T14:59:00Z')
    obs['prices']['history'] = {'intel': history}
    _, found, _ = run(obs)
    self.assertIn('mismatched-external:catalogue:intel', found)

  def test_stale_quote_in_session(self):
    """A holiday or a feed outage: in session by the clock, but the quote is hours old."""
    obs = self.obs('2026-11-09T15:00:00Z', 92.07, '2026-11-06T21:00:00Z')
    self.assertEqual(
      sessions.closing_reference(CATALOGUE, obs, 'intel', obs['prices']['assets']['intel']['providers']),
      'reference quote is not fresh',
    )

  def test_sessions(self):
    self.assertTrue(sessions.in_session('', timestamp('2026-11-09T15:00:00Z')))
    self.assertFalse(sessions.in_session('', timestamp('2026-11-07T15:00:00Z')))  # Saturday
    self.assertTrue(sessions.in_session('HK', timestamp('2026-11-09T03:00:00Z')))
    self.assertFalse(sessions.in_session('HK', timestamp('2026-11-09T09:00:00Z')))
    self.assertEqual(sessions.exchange({'external': {'yahoo': '0992.HK'}}), 'HK')
    self.assertIsNone(sessions.exchange({'external': {'yahoo': '7203.XX'}}))

  def test_continuous_references_are_always_fair(self):
    """Crypto, and tokenized stocks priced by CoinGecko, trade around the clock."""
    quotes = {'coingecko': {'usd': 1, 'as_of': '2026-11-07T04:45:00Z'}}
    self.assertIsNone(sessions.closing_reference(CATALOGUE, OBSERVATIONS, 'siren-bsc', quotes))


class SirenTest(unittest.TestCase):
  """siren-bsc: a one-slot gap against a bimodal CoinGecko aggregate (#383, #391, #399)."""

  def obs(self, history=None, providers=None):
    obs = copy.deepcopy(OBSERVATIONS)
    if history is not None:
      obs['prices']['history'] = {'siren-bsc': history}
    if providers is not None:
      obs['prices']['assets']['siren-bsc'] = {'providers': providers}
    return obs

  def test_one_slot_is_unconfirmed(self):
    report, found, suppressed = run(entries=[])
    self.assertIn('mismatched-external:catalogue:siren-bsc', markers())
    self.assertNotIn('mismatched-external:catalogue:siren-bsc', found)
    self.assertEqual(report['checks']['mismatched-external']['platforms']['notes']['unconfirmed'], ['siren-bsc'])
    self.assertFalse([fp for fp in found if fp.startswith('price:') and 'SIREN' in fp])

  def test_persisting_gap_fires_and_the_exception_holds_it(self):
    history = [{'ts': '2026-11-07T03:50:00Z', 'implied_usd': 0.0254, 'reference_usd': 0.0322}]
    _, found, _ = run(self.obs(history), entries=[])
    self.assertIn('mismatched-external:catalogue:siren-bsc', found)
    _, found, suppressed = run(self.obs(history))
    self.assertNotIn('mismatched-external:catalogue:siren-bsc', found)
    self.assertIn('mismatched-external:catalogue:siren-bsc', suppressed)

  def test_slots_that_dont_count(self):
    """Older than a day, or on the other side of the reference."""
    for row in [
      {'ts': '2026-11-05T03:50:00Z', 'implied_usd': 0.0254, 'reference_usd': 0.0322},
      {'ts': '2026-11-07T03:50:00Z', 'implied_usd': 0.0420, 'reference_usd': 0.0322},
      {'ts': '2026-11-07T03:50:00Z', 'implied_usd': 0.0310, 'reference_usd': 0.0322},
    ]:
      with self.subTest(row=row):
        _, found, _ = run(self.obs([row]), entries=[])
        self.assertNotIn('mismatched-external:catalogue:siren-bsc', found)

  def test_split_reference(self):
    providers = {'coingecko': {'usd': 0.0399}, 'coinmarketcap': {'usd': 0.0276}}
    history = [{'ts': '2026-11-07T03:50:00Z', 'implied_usd': 0.0254}]
    report, found, _ = run(self.obs(history, providers), entries=[])
    self.assertNotIn('mismatched-external:catalogue:siren-bsc', found)
    self.assertEqual(report['checks']['mismatched-external']['platforms']['notes']['reference_split'], ['siren-bsc'])


class ExceptionsTest(unittest.TestCase):
  """EWT and 1000CAT wait on a schema decision; the file holds them, with the PR that said so."""

  def test_held_by_the_file(self):
    _, found, suppressed = run()
    for fp in ('base-quote:mexc:perp:EWT_USDT', 'base-quote:bitget:usdt:1000CATUSDT'):
      with self.subTest(fp=fp):
        self.assertNotIn(fp, found)
        self.assertIn(fp, suppressed)

  def test_pending_decisions_say_so(self):
    entries = {entry['fingerprint']: entry for entry in exceptions.load()}
    self.assertIn('pending owner decision', entries['base-quote:mexc:perp:EWT_USDT']['reason'])
    self.assertIn('pending owner decision', entries['base-quote:bitget:usdt:1000CATUSDT']['reason'])

  def test_no_exception_for_what_a_rule_fixes(self):
    """A rule, not an exception, so a genuinely wrong ID or quote on these still reports."""
    globs = [entry['fingerprint'] for entry in exceptions.load()]
    for fp in ('base-quote:mexc:perp:HK0700_USDT', 'mismatched-external:catalogue:intel', 'mismatched-external:catalogue:applovin'):
      with self.subTest(fp=fp):
        self.assertIsNone(exceptions.suppressed_by({'fingerprint': fp}, exceptions.load()), globs)


if __name__ == '__main__':
  unittest.main()
