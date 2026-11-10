#!/usr/bin/env python3
"""Check `CLOSE_ONLY` in `scripts/gtrade.py` against gTrade's docs, app and open trades.

No backend field marks a close-only collateral: DAI's vaults still report `isActive`
true. This script reads the three places that do show it, and exits 1 when any
disagrees with `CLOSE_ONLY`, so the flag cannot go stale unnoticed:

- the docs' "Collateral availability by chain" table
  (`docs.gains.trade/gtrade-leveraged-trading/trade-collaterals.md`), which lists the
  collaterals each chain offers. A collateral the backend reports active but the docs
  leave out may have become close-only. A `CLOSE_ONLY` one the docs list may be open again;
- the trading app, which refuses opens by collateral symbol through an
  `<x>TradingDisabled` message (`daiTradingDisabled`: "DAI trading disabled"). It
  finds the key set in the app bundle and compares it with `CLOSE_ONLY`;
- each chain's `open-trades`, which must hold no trade or order in a `CLOSE_ONLY` vault
  created or increased after the block it went close-only (`CLOSE_ONLY_SINCE`).
  This sees only trades still open when it runs.

Read-only, no key, network required. `.github/workflows/gtrade-sync.yml` runs it weekly:

    PYTHONPATH=lib/src .venv/bin/python scripts/check_gtrade_close_only.py [--markdown PATH]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Mapping
import urllib.request

from gtrade import CHAINS, CLOSE_ONLY

DOCS = 'https://docs.gains.trade/gtrade-leveraged-trading/trade-collaterals.md'
APP = 'https://gains.trade/trading'
BACKEND = 'https://backend-{chain}.gains.trade/{path}'

CLOSE_ONLY_SINCE: dict[str, dict[str, int]] = {
  'DAI': {
    'arbitrum': 399_294_999,  # first block of 2025-11-12 UTC
    'polygon': 78_900_358,  # first block of 2025-11-12 UTC
  },
}
"""Per `CLOSE_ONLY` symbol, chain -> first block of the day it went close-only. No open
trade in the vault may be created or increased at or after it."""


def get(url: str) -> bytes:
  request = urllib.request.Request(url, headers={'User-Agent': 'tribulnation-catalogue'})
  with urllib.request.urlopen(request, timeout=60) as response:
    return response.read()


# --- sources -----------------------------------------------------------------

def docs_offered(markdown: str) -> dict[str, set[str]]:
  """Chain id -> upper-case collateral symbols from the docs' availability table."""
  _, _, rest = markdown.partition('Collateral availability by chain')
  offered: dict[str, set[str]] = {}
  for line in rest.splitlines():
    cells = [c.strip() for c in line.strip().strip('|').split('|')]
    if len(cells) != 2 or cells[0] in ('Chain', '') or set(cells[0]) <= set('-: '):
      if offered and not line.strip().startswith('|'):
        break
      continue
    offered[cells[0].lower()] = {s.replace('\\', '').strip(' $').upper() for s in cells[1].split(',') if s.strip()}
  return offered


def app_disabled(bundle: str) -> set[str]:
  """Upper-case prefixes of the app's `<x>TradingDisabled` messages (`dai` -> `DAI`)."""
  return {m.upper() for m in re.findall(r'"([a-z][A-Za-z0-9]*)TradingDisabled"\s*:', bundle)}


def app_bundle_url(html: str) -> str | None:
  m = re.search(r'["\'](?:\.?/)?(_next/static/chunks/pages/_app-[0-9a-f]+\.js)["\']', html)
  return f'https://gains.trade/{m.group(1)}' if m else None


def late_opens(trading_variables: Mapping[str, Any], open_trades: Iterable[Mapping[str, Any]],
               symbol: str, since: int) -> list[int]:
  """Blocks at which trades in `symbol`'s vault were created or increased at or after
  `since`, newest first."""
  indexes = {str(c.get('collateralIndex')) for c in trading_variables['collaterals'] if c['symbol'].upper() == symbol}
  blocks = []
  for t in open_trades:
    if str(t['trade'].get('collateralIndex')) not in indexes:
      continue
    info = t.get('tradeInfo', {})
    last = max(int(info.get('createdBlock') or 0), int(info.get('lastPosIncreaseBlock') or 0))
    if last >= since:
      blocks.append(last)
  return sorted(blocks, reverse=True)


# --- check -------------------------------------------------------------------

def findings(offered: Mapping[str, set[str]], active: Mapping[str, set[str]], vaults: Mapping[str, set[str]],
             disabled: set[str] | None, late: Mapping[tuple[str, str], list[int]]) -> list[str]:
  """Every disagreement with `CLOSE_ONLY`.

  `offered`: the docs table; `active`/`vaults`: per chain, the upper-case symbols of the
  backend's active vaults / of all its vaults; `disabled`: the app's disabled symbols
  (None when the bundle could not be read); `late`: (chain, symbol) -> late-open blocks.
  """
  close_only = {s.upper() for s in CLOSE_ONLY}
  out = []
  for chain in CHAINS:
    if chain not in offered:
      out.append(f'{chain}: the docs table has no row for this chain')
      continue
    for s in sorted(active.get(chain, set()) - offered[chain] - close_only):
      out.append(f'{chain}: {s} is active in the backend but the docs do not offer it: close-only? '
                 'If the app refuses opens too, add it to CLOSE_ONLY')
    for s in sorted(offered[chain] & close_only):
      out.append(f'{chain}: the docs offer {s} again, which CLOSE_ONLY marks close-only')
    for s in sorted(offered[chain] - active.get(chain, set())):
      out.append(f'{chain}: the docs offer {s} but the backend has no active {s} vault')
  if disabled is None:
    out.append('app: could not find the trading app bundle, so its disabled collaterals were not checked')
  elif disabled != close_only:
    out.append(f'app: refuses opens on {sorted(disabled) or "no collateral"}, CLOSE_ONLY lists {sorted(close_only)}')
  for symbol in sorted(close_only):
    since = CLOSE_ONLY_SINCE.get(symbol, {})
    for chain in CHAINS:
      if symbol not in vaults.get(chain, set()):
        continue
      if chain not in since:
        out.append(f'{chain}: {symbol} is in CLOSE_ONLY with no CLOSE_ONLY_SINCE block for this chain')
      elif late.get((chain, symbol)):
        blocks = late[(chain, symbol)]
        out.append(f'{chain}: {len(blocks)} open {symbol} trade(s) created or increased after it went close-only '
                   f'(newest at block {blocks[0]}): {symbol} may be open again')
  return out


def report(found: list[str]) -> str:
  if not found:
    return '### gTrade close-only\n\n`CLOSE_ONLY` agrees with the docs, the app and the open trades.\n'
  return ('### gTrade close-only\n\n`CLOSE_ONLY` in `scripts/gtrade.py` disagrees with the venue. '
          'Check the docs and app, then update it and regenerate:\n\n' + ''.join(f'- {f}\n' for f in found))


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  parser.add_argument('--markdown', type=Path, help='also write the report here')
  args = parser.parse_args()

  offered = docs_offered(get(DOCS).decode())
  bundle = app_bundle_url(get(APP).decode())
  disabled = app_disabled(get(bundle).decode()) if bundle else None
  active, vaults, late = {}, {}, {}
  for chain in CHAINS:
    tv = json.loads(get(BACKEND.format(chain=chain, path='trading-variables')))
    vaults[chain] = {c['symbol'].upper() for c in tv['collaterals']}
    active[chain] = {c['symbol'].upper() for c in tv['collaterals'] if c.get('isActive')}
    close_only_here = [s.upper() for s in CLOSE_ONLY if s.upper() in vaults[chain]]
    if close_only_here:
      trades = json.loads(get(BACKEND.format(chain=chain, path='open-trades')))
      for s in close_only_here:
        since = CLOSE_ONLY_SINCE.get(s, {}).get(chain)
        if since is not None:
          late[(chain, s)] = late_opens(tv, trades, s, since)
  found = findings(offered, active, vaults, disabled, late)
  text = report(found)
  if args.markdown:
    args.markdown.write_text(text)
  print(text)
  sys.exit(1 if found else 0)


if __name__ == '__main__':
  main()
