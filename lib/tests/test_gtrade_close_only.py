"""`scripts/check_gtrade_close_only.py`: `CLOSE_ONLY` in `scripts/gtrade.py` is checked
against gTrade's docs, app and open trades (weekly, in `.github/workflows/gtrade-sync.yml`).
These tests cover the parsing and the comparison offline."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))

import check_gtrade_close_only as check  # noqa: E402  # pyright: ignore[reportMissingImports]
import gtrade  # noqa: E402  # pyright: ignore[reportMissingImports]

DOCS = r"""
#### Collateral availability by chain

| Chain | Collaterals |
| - | - |
| Arbitrum | \$USDC, \$WETH, \$GNS |
| Polygon | \$USDC, \$WETH |
| Base | \$USDC, \$BtcUSD |
| MegaETH | \$USDm |

On Arbitrum, **ETH** in the menu opens a WETH trade. | Not | a row |
"""

OFFERED = {'arbitrum': {'USDC', 'WETH', 'GNS'}, 'polygon': {'USDC', 'WETH'}, 'base': {'USDC', 'BTCUSD'},
           'megaeth': {'USDM'}}
VAULTS = {'arbitrum': {'DAI', 'WETH', 'USDC', 'GNS'}, 'polygon': {'DAI', 'USDC', 'WETH'}, 'base': {'USDC', 'BTCUSD'},
          'megaeth': {'USDM'}}


def trade(collateral: int, created: int, increased: int = 0) -> dict:
  return {'trade': {'collateralIndex': str(collateral)},
          'tradeInfo': {'createdBlock': str(created), 'lastPosIncreaseBlock': str(increased)}}


class CloseOnlyCheckTest(unittest.TestCase):

  def test_docs_table(self):
    self.assertEqual(check.docs_offered(DOCS), OFFERED)

  def test_app_disabled_keys(self):
    bundle = '"tradingDisabled":"Trading disabled",x,"daiTradingDisabled":"DAI trading disabled","daiTradingDisabledTooltip":"y"'
    self.assertEqual(check.app_disabled(bundle), {'DAI'})
    self.assertEqual(check.app_bundle_url('<script src="./_next/static/chunks/pages/_app-23b5f4976f9cfe81.js">'),
                     'https://gains.trade/_next/static/chunks/pages/_app-23b5f4976f9cfe81.js')
    self.assertIsNone(check.app_bundle_url('<html></html>'))

  def test_late_opens_by_collateral_index(self):
    tv = {'collaterals': [{'symbol': 'DAI', 'collateralIndex': 1}, {'symbol': 'USDC', 'collateralIndex': 3}]}
    trades = [trade(1, 90), trade(1, 80, 120), trade(1, 100), trade(3, 500)]
    self.assertEqual(check.late_opens(tv, trades, 'DAI', 100), [120, 100])
    self.assertEqual(check.late_opens(tv, trades, 'DAI', 121), [])

  def test_agreement_has_no_findings(self):
    active = {c: set(v) for c, v in VAULTS.items()}
    self.assertEqual(check.findings(OFFERED, active, VAULTS, {'DAI'}, {('arbitrum', 'DAI'): [], ('polygon', 'DAI'): []}), [])

  def test_each_disagreement_is_reported(self):
    offered = {**OFFERED, 'arbitrum': {'USDC', 'DAI'}, 'base': {'USDC', 'BTCUSD', 'NEW'}}
    found = check.findings(offered, VAULTS, VAULTS, {'DAI', 'WETH'}, {('polygon', 'DAI'): [130, 120]})
    text = '\n'.join(found)
    self.assertIn('arbitrum: WETH is active in the backend but the docs do not offer it', text)
    self.assertIn('arbitrum: the docs offer DAI again', text)
    self.assertIn('base: the docs offer NEW but the backend has no active NEW vault', text)
    self.assertIn("app: refuses opens on ['DAI', 'WETH']", text)
    self.assertIn('polygon: 2 open DAI trade(s) created or increased after it went close-only (newest at block 130)', text)
    self.assertNotIn('megaeth', text)
    self.assertIn('could not find', '\n'.join(check.findings(OFFERED, VAULTS, VAULTS, None, {})))

  def test_every_close_only_vault_has_a_cutoff_block(self):
    """Adding a CLOSE_ONLY collateral needs its close-only block on every chain that has
    the vault, or the open-trades check cannot run there."""
    fixture = json.loads(gtrade.FIXTURE.read_text())
    for symbol in gtrade.CLOSE_ONLY:
      for chain, recorded in fixture.items():
        if any(c['symbol'] == symbol for c in recorded['collaterals']):
          self.assertIn(chain, check.CLOSE_ONLY_SINCE.get(symbol, {}), f'{symbol} on {chain}')


if __name__ == '__main__':
  unittest.main()
