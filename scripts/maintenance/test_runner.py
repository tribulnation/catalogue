"""The runner reports skips honestly, applies exceptions, and its CLI replays the fixtures."""

from pathlib import Path
import types
import unittest

from maintenance import catalogue, exceptions, observations, runner
from maintenance.finding import make

FIXTURES = Path(__file__).with_name('fixtures')


def group(names, inputs, findings, coverage):
  return types.SimpleNamespace(NAMES=names, INPUTS=inputs, run=lambda cat, obs: (findings, coverage))


class RunnerTest(unittest.TestCase):

  def setUp(self):
    self.catalogue = catalogue.load(FIXTURES / 'data')
    self.observations = observations.load(FIXTURES / 'observations')

  def test_fixture_loads(self):
    self.assertIn(('spot', 'BTCUSDT'), self.catalogue.instruments['bitget'])
    market = self.observations['listings']['bitget']['markets'][('spot', 'BTCUSDT')]
    self.assertEqual(market['price'], 100005)
    self.assertTrue(market['tradable'])
    self.assertNotIn('prices', self.observations)

  def test_complete_must_be_explicit(self):
    """A listing that doesn't say it is complete can't make a missing market stale."""
    raw = {'platforms': {
      'a': {'markets': []}, 'b': {'complete': 'yes', 'markets': []}, 'c': {'complete': True, 'markets': []},
    }}
    parsed = observations.parse_listings(raw)
    self.assertEqual({p: parsed[p]['complete'] for p in parsed}, {'a': False, 'b': False, 'c': True})

  def test_missing_input_is_skip(self):
    fake = group(('dead-external',), ('prices',), [], {})
    report = runner.run(self.catalogue, self.observations, [], groups=[fake])
    self.assertEqual(report['checks']['dead-external']['status'], 'skip')
    self.assertEqual(report['checks']['dead-external']['reason'], 'no prices observations')
    self.assertEqual(report['checks']['price']['reason'], 'not implemented')

  def test_findings_and_exceptions(self):
    found = [
      make('untranslated-asset', platform='bitget', subject='rACAD', severity='medium', summary='', evidence={}),
      make('untranslated-market', platform='bitget', subject='spot:RACADUSDT', severity='low', summary='',
           evidence={'venue_pair': {'base': 'rACAD', 'quote': 'USDT'}}),
      make('untranslated-market', platform='bitget', subject='spot:NEWUSDT', severity='medium', summary='',
           evidence={'venue_pair': {'base': 'NEW', 'quote': 'USDT'}}),
    ]
    fake = group(
      ('untranslated-asset', 'untranslated-market'), ('listings',), found,
      {'untranslated-asset': {'ran': ['bitget'], 'skip': {}}, 'untranslated-market': {'ran': ['bitget'], 'skip': {'kraken': 'not read'}}},
    )
    report = runner.run(self.catalogue, self.observations, exceptions.load(), groups=[fake])
    self.assertEqual([f['fingerprint'] for f in report['findings']], ['untranslated-market:bitget:spot:NEWUSDT'])
    self.assertEqual(report['checks']['untranslated-market']['found'], 1)
    self.assertEqual(report['checks']['untranslated-market']['suppressed'], 1)
    self.assertEqual(report['checks']['untranslated-market']['platforms']['skip'], {'kraken': 'not read'})
    self.assertEqual(report['checks']['untranslated-asset']['status'], 'ran')

  def test_only(self):
    report = runner.run(self.catalogue, self.observations, [], only=['price'])
    self.assertEqual(list(report['checks']), ['price'])
    with self.assertRaises(ValueError):
      runner.run(self.catalogue, self.observations, [], only=['client-validation'])


class CliTest(unittest.TestCase):

  def test_fixtures_match_the_recorded_result(self):
    import maintain
    code = maintain.main([
      '--data', str(FIXTURES / 'data'),
      '--observations', str(FIXTURES / 'observations'),
      '--expect', str(FIXTURES / 'expected.json'),
    ])
    self.assertEqual(code, 0)


if __name__ == '__main__':
  unittest.main()
