"""`maintenance/exceptions.toml` keeps catalogue-ops' semantics, and every entry is justified."""

import tomllib
import unittest

from maintenance import exceptions
from maintenance.finding import make
from maintenance.test_finding import markers


def untranslated_market(market: str, base: str, quote: str = 'USDT'):
  return make(
    'untranslated-market', platform='bitget', subject=f'spot:{market}', severity='low', summary='',
    evidence={'venue_pair': {'base': base, 'quote': quote}},
  )


def untranslated_asset(asset: str):
  return make('untranslated-asset', platform='bitget', subject=asset, severity='medium', summary='', evidence={})


class FileTest(unittest.TestCase):

  def test_file_is_valid(self):
    raw = tomllib.loads(exceptions.FILE.read_text()).get('exception', [])
    self.assertEqual(exceptions.errors(raw), [])

  def test_every_entry_matches_a_published_finding_or_is_dormant(self):
    """An entry nothing matches is dead weight unless it says it is dormant."""
    stale = exceptions.unmatched(exceptions.load(), markers())
    self.assertEqual([entry['fingerprint'] for entry in stale], [])


class SemanticsTest(unittest.TestCase):

  entries = [exceptions.Exception_(fingerprint='untranslated-asset:bitget:r[A-Z]*', reason='rTokens', ref='#147')]

  def test_glob_is_case_sensitive(self):
    """`rACAD` is an rToken; `RAY` is not."""
    self.assertIsNotNone(exceptions.suppressed_by(untranslated_asset('rACAD'), self.entries))
    self.assertIsNone(exceptions.suppressed_by(untranslated_asset('RAY'), self.entries))

  def test_asset_exception_covers_its_markets(self):
    findings = [untranslated_asset('rACAD'), untranslated_market('RACADUSDT', 'rACAD'), untranslated_market('RAYUSDT', 'RAY')]
    split = exceptions.apply(findings, self.entries)
    self.assertEqual([f['fingerprint'] for f in split['findings']], ['untranslated-market:bitget:spot:RAYUSDT'])
    self.assertEqual(
      {f['fingerprint']: f['exception'] for f in split['suppressed']},
      {
        'untranslated-asset:bitget:rACAD': 'untranslated-asset:bitget:r[A-Z]*',
        'untranslated-market:bitget:spot:RACADUSDT': 'untranslated-asset:bitget:rACAD',
      },
    )

  def test_market_alone_is_not_covered(self):
    """Without the asset finding in the same run (it was translated), the market still reports."""
    split = exceptions.apply([untranslated_market('RACADUSDT', 'rACAD')], self.entries)
    self.assertEqual(len(split['findings']), 1)

  def test_errors(self):
    self.assertEqual(len(exceptions.errors([{'fingerprint': 'price:x:y', 'reason': 'r'}])), 1)
    self.assertEqual(len(exceptions.errors([{'fingerprint': 'price:x:y', 'reason': ' ', 'ref': '#1'}])), 1)
    self.assertEqual(len(exceptions.errors([{'fingerprint': 'nope:x:y', 'reason': 'r', 'ref': '#1'}])), 1)
    self.assertEqual(len(exceptions.errors([{'fingerprint': 'price:x:y', 'reason': 'r', 'ref': '#1', 'until': 1}])), 1)
    self.assertEqual(exceptions.errors([{'fingerprint': '*-external:catalogue:x', 'reason': 'r', 'ref': 'tribulnation/catalogue#391'}]), [])

  def test_dormant(self):
    entries = [exceptions.Exception_(fingerprint='price:kraken:spot:NOPE', reason='r', ref='#1', dormant=True)]
    self.assertEqual(exceptions.unmatched(entries, []), [])


if __name__ == '__main__':
  unittest.main()
