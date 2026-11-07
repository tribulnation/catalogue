#!/usr/bin/env python3
"""Generate `data/instruments/perpetual/gtrade.json` from gTrade's public backend.

gTrade (Gains Network) lists the same pairs on several chains, and on each chain once
per collateral vault. Every vault has its own open interest, funding and borrowing, so
each (chain, collateral, pair) is its own instrument: `<chain>-<collateral>:<FROM>/<TO>`,
e.g. `arbitrum-usdc:BTC/USD`, with `exchange` the `<chain>-<collateral>` part.

The input is each chain's `GET https://backend-<chain>.gains.trade/trading-variables`
(read-only, no key). A recording of the fields this script reads is committed as
`scripts/gtrade_fixture.json`, so the file can be rebuilt, and checked in CI, offline:

    # rebuild the instruments from the recorded fixture
    PYTHONPATH=lib/src .venv/bin/python scripts/gtrade.py

    # re-record the fixture from the live backend, then rebuild
    PYTHONPATH=lib/src .venv/bin/python scripts/gtrade.py --refresh

    # exit 1 when the committed file differs from what the fixture gives (CI runs
    # this through lib/tests/test_gtrade.py)
    PYTHONPATH=lib/src .venv/bin/python scripts/gtrade.py --check

Base and quote assets come from `data/asset_translations/gtrade.json` (gTrade ticker,
without the `_1` suffix of a second listing, -> catalogue asset id). That mapping is
reviewed by hand: base assets were matched by price against other venues, and the
DEGEN pairs, 1000x tokens, RNDR, TON, DIA, HG and the FX legs were set by hand. A listed
pair whose ticker is neither mapped nor in `EXCLUDED` fails the run with the list of
tickers, instead of being guessed.

Settlement is the vault's collateral, resolved by its contract address through the
chain's own asset translations (`data/asset_translations/<chain>.json`).

A pair is listed in a vault when:
- the chain lists it: `pairInfos.maxLeverages[i]` is not 1 (1 marks a delisted pair).
  MegaETH reports 1 for every pair, so there a pair is listed when any active vault
  charges it funding or borrowing, or holds open interest in it;
- and the vault gives it an open-interest cap (`pairOis[i].beforeV10.max` > 0).

`quote` is the index currency (`usd`, or the FX pair's quote). `quanto` is left out when
the collateral is pegged to the quote; dollar pairs on a non-dollar collateral (WETH,
GNS) are `quanto: false`, the venue converting at the collateral's price; pairs quoted in
another currency (USD/JPY, EUR/AUD, ...) are `quanto: true`: P&L is paid as
size x (price - open price) in the collateral, with no exchange rate applied.

DEGEN pairs (`BTCDEGEN/USD`, ...) track the same index as the plain pair but trade in
gTrade's `crypto-degen` group (500x leverage, different fees). The schema has no field
for that, so they stay separate instruments told apart by their own id.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping
import urllib.request

from instrument_urls import gtrade_url

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUTPUT = DATA / 'instruments' / 'perpetual' / 'gtrade.json'
FIXTURE = Path(__file__).with_name('gtrade_fixture.json')

CHAINS = ('arbitrum', 'base', 'polygon', 'megaeth')
"""Chains gTrade runs on, by catalogue platform id (also the backend's subdomain)."""
BACKEND = 'https://backend-{chain}.gains.trade/trading-variables'

EXCLUDED = {
  'BRUN': 'listed pair whose underlying could not be identified',
  'BVIV': 'Volmex implied-volatility index; no catalogue asset',
  'EVIV': 'Volmex implied-volatility index; no catalogue asset',
}
"""Listed tickers deliberately left out, with the reason."""

_SECOND_LISTING = re.compile(r'_\d+$')
"""`TSLA_1` is a second listing of TSLA: same asset, its own pair index."""


# --- recording ---------------------------------------------------------------

def _int(x: Any) -> int:
  return int(str(x or 0))


def record(raw: Mapping[str, Any]) -> dict[str, Any]:
  """The fields of one chain's `trading-variables` response that the generator reads.

  `pairs[i]` is `[from, to, groupIndex, maxLeverage]`; a vault's `pairs[i]` is
  `[oiCap, fundingFeesEnabled, borrowingRatePerSecondP, oiTokens]`, all aligned on
  gTrade's pair index.
  """
  max_leverages = raw['pairInfos']['maxLeverages']
  pairs = [
    [p['from'], p['to'], _int(p['groupIndex']), _int(max_leverages[i]) if i < len(max_leverages) else 1]
    for i, p in enumerate(raw['pairs'])
  ]
  vaults = []
  for c in raw['collaterals']:
    ois = c['pairOis']
    funding = c['fundingFees']['pairParams']
    borrowing = c['borrowingFees'].get('v2', {}).get('pairParams', [])
    rows = []
    for i in range(len(pairs)):
      oi = ois[i] if i < len(ois) else {}
      tokens = oi.get('token', {})
      rows.append([
        str(_int(oi.get('beforeV10', {}).get('max'))),
        bool(funding[i].get('fundingFeesEnabled')) if i < len(funding) else False,
        str(_int(borrowing[i].get('borrowingRatePerSecondP'))) if i < len(borrowing) else '0',
        str(_int(tokens.get('oiLongToken')) + _int(tokens.get('oiShortToken'))),
      ])
    vaults.append({'symbol': c['symbol'], 'address': c['collateral'], 'active': bool(c.get('isActive')), 'pairs': rows})
  return {
    'refreshed': raw.get('lastRefreshed'),
    'groups': [g['name'] for g in raw['groups']],
    'pairs': pairs,
    'collaterals': vaults,
  }


def fetch(chain: str) -> dict[str, Any]:
  request = urllib.request.Request(BACKEND.format(chain=chain), headers={'User-Agent': 'tribulnation-catalogue'})
  with urllib.request.urlopen(request, timeout=60) as response:
    return json.load(response)


def dump_fixture(fixture: Mapping[str, Any]) -> str:
  """JSON with one pair per line, so a refresh diffs readably."""
  def rows(items: list, indent: str) -> str:
    return '[\n' + ',\n'.join(f'{indent}  {json.dumps(r)}' for r in items) + f'\n{indent}]'
  chains = []
  for chain, f in fixture.items():
    vaults = ',\n'.join(
      '      {' + ''.join(f'{json.dumps(k)}: {json.dumps(v)}, ' for k, v in c.items() if k != 'pairs')
      + f'"pairs": {rows(c["pairs"], "      ")}}}'
      for c in f['collaterals']
    )
    chains.append(
      f'  {json.dumps(chain)}: {{\n'
      f'    "refreshed": {json.dumps(f["refreshed"])},\n'
      f'    "groups": {json.dumps(f["groups"])},\n'
      f'    "pairs": {rows(f["pairs"], "    ")},\n'
      f'    "collaterals": [\n{vaults}\n    ]\n'
      f'  }}'
    )
  return '{\n' + ',\n'.join(chains) + '\n}\n'


# --- generation --------------------------------------------------------------

def listed(chain: Mapping[str, Any]) -> list[list[bool]]:
  """`[vault][pair]`: whether each active vault lists each pair (module docstring)."""
  pairs = chain['pairs']
  vaults = [c for c in chain['collaterals'] if c['active']]
  if all(p[3] == 1 for p in pairs):
    on_chain = [
      any(c['pairs'][i][1] or int(c['pairs'][i][2]) > 0 or int(c['pairs'][i][3]) > 0 for c in vaults)
      for i in range(len(pairs))
    ]
  else:
    on_chain = [p[3] != 1 for p in pairs]
  return [[on_chain[i] and int(c['pairs'][i][0]) > 0 for i in range(len(pairs))] for c in vaults]


def _translations(platform: str) -> dict[str, str]:
  path = DATA / 'asset_translations' / f'{platform}.json'
  return json.loads(path.read_text()) if path.exists() else {}


def _pegged_to(asset: str) -> str | None:
  record = json.loads((DATA / 'assets' / f'{asset}.json').read_text())
  return (record.get('pegged_to') or {}).get('asset')


def instruments(fixture: Mapping[str, Any], tickers: Mapping[str, str] | None = None) -> dict[str, dict[str, Any]]:
  """The perpetuals the fixture lists, keyed and ordered as in the committed file.

  Raises `ValueError` naming every listed ticker or collateral with no mapping.
  """
  tickers = _translations('gtrade') if tickers is None else tickers
  out: dict[str, dict[str, Any]] = {}
  unknown: dict[str, set[str]] = {}
  for chain_id in sorted(fixture):
    chain = fixture[chain_id]
    addresses = {k.lower(): v for k, v in _translations(chain_id).items()}
    vaults = [c for c in chain['collaterals'] if c['active']]
    for vault, flags in zip(vaults, listed(chain)):
      exchange = f'{chain_id}-{vault["symbol"].lower()}'
      settlement = addresses.get(vault['address'].lower())
      if settlement is None:
        unknown.setdefault(f'collateral {vault["address"]} ({vault["symbol"]})', set()).add(chain_id)
        continue
      peg = _pegged_to(settlement)
      for i, (base_ticker, quote_ticker, _, _) in enumerate(chain['pairs']):
        if not flags[i]:
          continue
        ticker = _SECOND_LISTING.sub('', base_ticker)
        if ticker in EXCLUDED:
          continue
        missing = [t for t in (ticker, quote_ticker) if t not in tickers]
        for t in missing:
          unknown.setdefault(t, set()).add(f'{exchange}:{base_ticker}/{quote_ticker}')
        if missing:
          continue
        id = f'{exchange}:{base_ticker}/{quote_ticker}'
        inst: dict[str, Any] = {'exchange': exchange, 'base': tickers[ticker], 'quote': tickers[quote_ticker], 'settlement': settlement}
        if inst['quote'] != peg:
          inst['quanto'] = inst['quote'] != 'usd'
        url = gtrade_url(id, inst, {})
        if url is not None:
          inst['url'] = url
        out[id] = inst
  if unknown:
    lines = [f'  {t}: {", ".join(sorted(where)[:4])}{" ..." if len(where) > 4 else ""}' for t, where in sorted(unknown.items())]
    raise ValueError(
      'gTrade lists tickers with no mapping. Add them to data/asset_translations/gtrade.json '
      '(or EXCLUDED in scripts/gtrade.py, with a reason); collaterals go in the chain\'s '
      'asset translations:\n' + '\n'.join(lines)
    )
  return dict(sorted(out.items(), key=lambda kv: kv[0].split(':', 1)))


def render(items: Mapping[str, Any]) -> str:
  return json.dumps(items, indent=2, ensure_ascii=False) + '\n'


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  mode = parser.add_mutually_exclusive_group()
  mode.add_argument('--refresh', action='store_true', help='re-record the fixture from the live backend first')
  mode.add_argument('--check', action='store_true', help='exit 1 if the committed file differs from the fixture\'s')
  args = parser.parse_args()

  if args.refresh:
    fixture = {chain: record(fetch(chain)) for chain in CHAINS}
    FIXTURE.write_text(dump_fixture(fixture))
    print(f'Recorded {FIXTURE.relative_to(ROOT)}')
  fixture = json.loads(FIXTURE.read_text())
  try:
    text = render(instruments(fixture))
  except ValueError as e:
    sys.exit(str(e))
  if args.check:
    if OUTPUT.read_text() != text:
      sys.exit(f'{OUTPUT.relative_to(ROOT)} differs from scripts/gtrade.py\'s output; run it and commit the result')
    print(f'{OUTPUT.relative_to(ROOT)} matches the fixture')
    return
  OUTPUT.write_text(text)
  print(f'Wrote {len(json.loads(text))} instruments to {OUTPUT.relative_to(ROOT)}')


if __name__ == '__main__':
  main()
