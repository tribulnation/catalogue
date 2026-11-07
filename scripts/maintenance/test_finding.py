"""Fingerprints stay byte-identical to catalogue-ops' issue markers."""

from pathlib import Path
import unittest

from maintenance.finding import CHECKS, fingerprint, make, market_subject, parse

MARKERS = Path(__file__).with_name('fixtures') / 'issue_markers.txt'


def markers() -> list[str]:
  """Every fingerprint catalogue-ops published."""
  return [line for line in MARKERS.read_text().splitlines() if line and not line.startswith('#')]


class FingerprintTest(unittest.TestCase):

  def test_real_markers(self):
    """Each shape of subject, built from its parts, gives the published marker."""
    cases = [
      (('untranslated-market', 'hyperliquid', market_subject('io', 'io:MU')), 'untranslated-market:hyperliquid:io:io:MU'),
      (('untranslated-market', 'hyperliquid', market_subject('', '0G')), 'untranslated-market:hyperliquid::0G'),
      (('untranslated-market', 'hyperliquid', market_subject('spot', 'QTC/USDC:1188')), 'untranslated-market:hyperliquid:spot:QTC/USDC:1188'),
      (('untranslated-market', 'lighter', market_subject('perp', '8286')), 'untranslated-market:lighter:perp:8286'),
      (('stale-listing', 'kraken', market_subject('spot', 'VELODROMEEUR')), 'stale-listing:kraken:spot:VELODROMEEUR'),
      (('stale-listing', 'coinbase', market_subject('intx', '1000BONK-PERP-INTX')), 'stale-listing:coinbase:intx:1000BONK-PERP-INTX'),
      (('base-quote', 'mexc', market_subject('perp', 'HK0992_USDT')), 'base-quote:mexc:perp:HK0992_USDT'),
      (('base-quote', 'bitget', market_subject('usdt', '1000CATUSDT')), 'base-quote:bitget:usdt:1000CATUSDT'),
      (('price', 'coinbase', market_subject('spot', 'BLAST-USD')), 'price:coinbase:spot:BLAST-USD'),
      (('mismatched-external', 'catalogue', 'siren-bsc'), 'mismatched-external:catalogue:siren-bsc'),
      (('dead-external', 'catalogue', 'telcoin'), 'dead-external:catalogue:telcoin'),
      (('missing-external', 'catalogue', 'openai'), 'missing-external:catalogue:openai'),
      (('untranslated-asset', 'mexc', 'TSCOSTOCK'), 'untranslated-asset:mexc:TSCOSTOCK'),
    ]
    published = set(markers())
    for args, marker in cases:
      with self.subTest(marker=marker):
        self.assertEqual(fingerprint(*args), marker)
        self.assertIn(marker, published)

  def test_every_marker_round_trips(self):
    """Splitting at the first two colons and joining again gives every published marker back."""
    found = markers()
    self.assertGreater(len(found), 2000)
    for marker in found:
      self.assertEqual(fingerprint(*parse(marker)), marker)
      self.assertIn(parse(marker)[0], (*CHECKS, 'client-validation'))

  def test_make(self):
    f = make('stale-listing', platform='kraken', subject='spot:X', severity='low', summary='s', evidence={'a': 1})
    self.assertEqual(f['fingerprint'], 'stale-listing:kraken:spot:X')
    with self.assertRaises(ValueError):
      make('client-validation', platform='bitget', subject='earn', severity='high', summary='s', evidence={})


if __name__ == '__main__':
  unittest.main()
