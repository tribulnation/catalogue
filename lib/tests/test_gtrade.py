"""gTrade's instruments are generated, not hand-written: `scripts/gtrade.py` rebuilds
`data/instruments/perpetual/gtrade.json` from a recording of gTrade's backend
(`scripts/gtrade_fixture.json`), and CI fails when the committed file drifts from it.

Refresh both with `PYTHONPATH=lib/src .venv/bin/python scripts/gtrade.py --refresh`."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))

import gtrade  # noqa: E402


def chain(pairs: list[list], vaults: dict[str, list[list]]) -> dict:
  """A minimal recorded chain: `pairs` as `[from, to, group, maxLeverage]`, each vault's
  rows as `[oiCap, fundingEnabled, borrowingRate, oiTokens]`."""
  return {
    'refreshed': None, 'groups': ['crypto'], 'pairs': pairs,
    'collaterals': [{'symbol': s, 'address': a, 'active': True, 'pairs': rows} for (s, a), rows in
                    ((tuple(k.split('@')), v) for k, v in vaults.items())],
  }


USDC = 'USDC@0xaf88d065e77c8cC2239327C5EDb3A432268e5831'
WETH = 'WETH@0x82aF49447D8a07e3bd95BD0d56f35241523fBab1'
TICKERS = {'BTC': 'bitcoin', 'BTCDEGEN': 'bitcoin', 'TSLA': 'tesla', 'USD': 'usd', 'JPY': 'japanese-yen'}


class GtradeTest(unittest.TestCase):

  def test_committed_file_matches_generator(self):
    """The committed file is exactly what the generator makes from the fixture."""
    fixture = json.loads(gtrade.FIXTURE.read_text())
    self.assertEqual(gtrade.OUTPUT.read_text(), gtrade.render(gtrade.instruments(fixture)),
                     'gtrade.json differs from scripts/gtrade.py output; run the script and commit the result')

  def test_fixture_is_in_its_canonical_form(self):
    """A hand-edited fixture is caught: it must read back as `dump_fixture` writes it."""
    text = gtrade.FIXTURE.read_text()
    self.assertEqual(text, gtrade.dump_fixture(json.loads(text)))

  def test_listing_vaults_and_quanto(self):
    """One instrument per vault; delisted pairs (maxLeverage 1) and vaults without an OI
    cap are left out; FX is quanto, dollar pairs on WETH are not."""
    fx = {'arbitrum': chain(
      [['BTC', 'USD', 0, 0], ['ETH', 'USD', 0, 1], ['USD', 'JPY', 0, 0], ['TSLA_1', 'USD', 0, 0]],
      {USDC: [['1', False, '0', '0'], ['1', False, '0', '0'], ['1', False, '0', '0'], ['0', False, '0', '0']],
       WETH: [['1', False, '0', '0'], ['1', False, '0', '0'], ['1', False, '0', '0'], ['1', False, '0', '0']]},
    )}
    out = gtrade.instruments(fx, TICKERS)
    self.assertEqual(list(out), ['arbitrum-usdc:BTC/USD', 'arbitrum-usdc:USD/JPY',
                                 'arbitrum-weth:BTC/USD', 'arbitrum-weth:TSLA_1/USD', 'arbitrum-weth:USD/JPY'])
    self.assertNotIn('quanto', out['arbitrum-usdc:BTC/USD'])
    self.assertIs(out['arbitrum-usdc:USD/JPY']['quanto'], True)
    self.assertIs(out['arbitrum-weth:BTC/USD']['quanto'], False)
    self.assertEqual(out['arbitrum-weth:TSLA_1/USD']['base'], 'tesla')
    self.assertNotIn('url', out['arbitrum-weth:TSLA_1/USD'])
    self.assertEqual(out['arbitrum-usdc:BTC/USD']['settlement'], 'usd-coin')

  def test_chain_reporting_max_leverage_1_everywhere_lists_by_activity(self):
    """MegaETH reports maxLeverage 1 for every pair; there funding, borrowing or open
    interest marks a listed pair."""
    fx = {'arbitrum': chain(
      [['BTC', 'USD', 0, 1], ['TSLA', 'USD', 0, 1], ['USD', 'JPY', 0, 1]],
      {USDC: [['1', True, '0', '0'], ['1', False, '0', '0'], ['1', False, '0', '7']]},
    )}
    self.assertEqual(list(gtrade.instruments(fx, TICKERS)), ['arbitrum-usdc:BTC/USD', 'arbitrum-usdc:USD/JPY'])

  def test_unknown_ticker_fails_with_list(self):
    """A new listing is not guessed: the run fails naming every unmapped ticker."""
    fx = {'arbitrum': chain(
      [['NEWCOIN', 'USD', 0, 0], ['BRUN', 'USD', 0, 0], ['BTC', 'CHF', 0, 0]],
      {USDC: [['1', False, '0', '0']] * 3},
    )}
    with self.assertRaises(ValueError) as e:
      gtrade.instruments(fx, TICKERS)
    message = str(e.exception)
    self.assertIn('NEWCOIN: arbitrum-usdc:NEWCOIN/USD', message)
    self.assertIn('CHF: arbitrum-usdc:BTC/CHF', message)
    self.assertNotIn('BRUN', message)

  def test_degen_pairs_are_separate_instruments(self):
    """DEGEN pairs share the base asset but keep their own id (no schema field marks them)."""
    out = json.loads(gtrade.OUTPUT.read_text())
    degen = out['arbitrum-usdc:BTCDEGEN/USD']
    self.assertEqual(degen['base'], out['arbitrum-usdc:BTC/USD']['base'])


if __name__ == '__main__':
  unittest.main()
