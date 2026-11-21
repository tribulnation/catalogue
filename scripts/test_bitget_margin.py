"""The Bitget margin sync keeps only translated crypto pairs that trade a catalogued spot book."""

import unittest

from bitget_margin import VenuePair, plan, refusal

TRANSLATIONS = {'LIT': 'lighter', 'USDT': 'tether', 'BTC': 'bitcoin'}
SPOT = {
  'LITUSDT': {'exchange': 'spot', 'base': 'lighter', 'quote': 'tether'},
  'BTCUSDT': {'exchange': 'spot', 'base': 'bitcoin', 'quote': 'tether'},
}


def pair(symbol: str, base: str, *, status: str = 'online', type: str = 'crypto') -> VenuePair:
  """A venue margin pair quoted in USDT."""
  return VenuePair(symbol=symbol, baseCoin=base, quoteCoin='USDT', status=status, instrumentType=type)


class PlanTest(unittest.TestCase):
  """`plan` gates venue pairs and flips `delisted`."""

  def test_gates(self):
    """Stock tokens, offline pairs, untranslated coins and pairs without a spot book are skipped."""
    result = plan([
      pair('LITUSDT', 'LIT'),
      pair('RAAPLUSDT', 'rAAPL', type='stock'),
      pair('BTCUSDT', 'BTC', status='limit_open'),
      pair('GRAMUSDT', 'GRAM'),
      pair('BTCUSDC', 'BTC'),
    ], translations=TRANSLATIONS, spot=SPOT, existing={})
    self.assertEqual(result['added'], ['LITUSDT'])
    self.assertEqual(result['instruments'], {'LITUSDT': {'exchange': 'margin', 'base': 'lighter', 'quote': 'tether'}})
    self.assertEqual(result['skipped'], {
      'BTCUSDC': 'no-spot-pair', 'BTCUSDT': 'not-online', 'GRAMUSDT': 'untranslated', 'RAAPLUSDT': 'not-crypto',
    })

  def test_delist_and_relist(self):
    """A pair the venue drops is flagged, never removed; one that returns is unflagged."""
    existing = {
      'BTCUSDT': {'exchange': 'margin', 'base': 'bitcoin', 'quote': 'tether'},
      'LITUSDT': {'exchange': 'margin', 'base': 'lighter', 'quote': 'tether', 'delisted': True},
    }
    result = plan([pair('LITUSDT', 'LIT')], translations=TRANSLATIONS, spot=SPOT, existing=existing)
    self.assertEqual((result['added'], result['delisted'], result['relisted']), ([], ['BTCUSDT'], ['LITUSDT']))
    self.assertTrue(result['instruments']['BTCUSDT']['delisted'])
    self.assertNotIn('delisted', result['instruments']['LITUSDT'])
    self.assertNotIn('delisted', existing['BTCUSDT'])


  def test_offline_pair_is_not_delisted(self):
    """A catalogued pair the venue lists in another status keeps its flag and is reported."""
    existing = {'BTCUSDT': {'exchange': 'margin', 'base': 'bitcoin', 'quote': 'tether'}}
    result = plan([pair('BTCUSDT', 'BTC', status='limit_open')], translations=TRANSLATIONS, spot=SPOT, existing=existing)
    self.assertEqual((result['delisted'], result['relisted']), ([], []))
    self.assertEqual(result['offline'], {'BTCUSDT': 'limit_open'})
    self.assertEqual(result['instruments'], existing)


class RefusalTest(unittest.TestCase):
  """`--write` refuses replies that look truncated."""

  def test_empty_response(self):
    """No venue pairs at all is refused rather than delisting everything."""
    existing = {'BTCUSDT': {'exchange': 'margin', 'base': 'bitcoin', 'quote': 'tether'}}
    result = plan([], translations=TRANSLATIONS, spot=SPOT, existing=existing)
    self.assertEqual(result['delisted'], ['BTCUSDT'])
    self.assertIsNotNone(refusal([], result, existing=existing))

  def test_mass_delisting(self):
    """Delisting more than the allowed share of listed pairs is refused; a few are accepted."""
    existing = {f'C{i}USDT': {'exchange': 'margin', 'base': 'bitcoin', 'quote': 'tether'} for i in range(100)}
    pairs = [pair(f'C{i}USDT', 'BTC') for i in range(80)]
    result = plan(pairs, translations=TRANSLATIONS, spot=SPOT, existing=existing)
    self.assertEqual(len(result['delisted']), 20)
    self.assertIsNotNone(refusal(pairs, result, existing=existing))
    pairs = [pair(f'C{i}USDT', 'BTC') for i in range(95)]
    result = plan(pairs, translations=TRANSLATIONS, spot=SPOT, existing=existing)
    self.assertIsNone(refusal(pairs, result, existing=existing))


if __name__ == '__main__':
  unittest.main()
