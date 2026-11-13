"""Exercise the perpetual-quote guard (scripts/check_perp_quotes.py) on small data
folders, and run it on the real one: CI's `unittest discover -s lib/tests` fails on a
Lighter or Hyperliquid perpetual quoted in USDC."""

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))

from check_perp_quotes import errors, load_exceptions  # noqa: E402  # pyright: ignore[reportMissingImports]


def write(root: Path, platform: str, perps: dict[str, dict], assets: dict[str, str]):
  """A minimal data folder: one platform's perpetuals and the assets' categories."""
  (root / 'instruments' / 'perpetual').mkdir(parents=True)
  (root / 'assets').mkdir()
  (root / 'instruments' / 'perpetual' / f'{platform}.json').write_text(json.dumps(perps))
  for id, category in assets.items():
    (root / 'assets' / f'{id}.json').write_text(json.dumps({'id': id, 'category': category}))


def perp(base: str, quote: str) -> dict:
  return {'exchange': 'perp', 'base': base, 'quote': quote, 'settlement': 'usd-coin'}


class PerpQuoteTest(unittest.TestCase):

  def test_usdc_quoted_lighter_perp_fails(self):
    """A new Lighter listing copied with the settlement coin as quote is caught, with a hint."""
    with TemporaryDirectory() as tmp:
      root = Path(tmp)
      write(root, 'lighter', {'1': perp('bitcoin', 'tether'), '4097': perp('pearl', 'usd-coin'),
                              '192': perp('openai', 'usd-coin')}, {'bitcoin': 'crypto', 'pearl': 'crypto', 'openai': 'stock'})
      found = {line.split(' ')[0]: line for line in errors(root, {})}
      self.assertEqual(sorted(found), ['lighter:192', 'lighter:4097'])
      self.assertIn('"tether" for a crypto asset', found['lighter:4097'])
      self.assertIn('"usd" for a stock asset', found['lighter:192'])

  def test_usdc_quoted_hyperliquid_perp_fails(self):
    with TemporaryDirectory() as tmp:
      root = Path(tmp)
      write(root, 'hyperliquid', {'NEW': perp('new', 'usd-coin')}, {'new': 'crypto'})
      self.assertEqual(len(errors(root, {})), 1)

  def test_exception_with_reason_passes(self):
    with TemporaryDirectory() as tmp:
      root = Path(tmp)
      write(root, 'hyperliquid', {'HYPE': perp('hyperliquid', 'usd-coin')}, {'hyperliquid': 'crypto'})
      self.assertEqual(errors(root, {'hyperliquid:HYPE': 'priced off its USDC spot book'}), [])
      self.assertEqual(len(errors(root, {'hyperliquid:HYPE': ' '})), 1)

  def test_stale_exception_fails(self):
    """An exception whose market no longer quotes USDC must be removed."""
    with TemporaryDirectory() as tmp:
      root = Path(tmp)
      write(root, 'hyperliquid', {'HYPE': perp('hyperliquid', 'tether')}, {'hyperliquid': 'crypto'})
      found = errors(root, {'hyperliquid:HYPE': 'reason', 'hyperliquid:GONE': 'reason'})
      self.assertEqual(len(found), 2)
      self.assertTrue(all('remove it' in line for line in found))

  def test_other_platforms_are_not_checked(self):
    """Venues whose index can be USDC (Binance BTCUSDC, Aster BTCUSDC) are out of scope."""
    with TemporaryDirectory() as tmp:
      root = Path(tmp)
      write(root, 'aster', {'BTCUSDC': perp('bitcoin', 'usd-coin')}, {'bitcoin': 'crypto'})
      self.assertEqual(errors(root, {}), [])

  def test_catalogue_passes(self):
    """The repository's own data passes with its listed exceptions."""
    self.assertEqual(errors(ROOT / 'data', load_exceptions()), [])


if __name__ == '__main__':
  unittest.main()
