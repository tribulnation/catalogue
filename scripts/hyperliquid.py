#!/usr/bin/env python3
"""Compare `data/instruments/perpetual/hyperliquid.json` with the venue and apply the safe part.

Hyperliquid's info API (POST https://api.hyperliquid.xyz/info, read-only, no key) lists
every perp dex (`perpDexs`) and, per dex, its markets and their collateral
(`metaAndAssetCtxs` with `dex`). This script reads both and reports:

- every catalogue perpetual whose `delisted` flag disagrees with the venue's
  `isDelisted` (the same comparison as scripts/check_hyperliquid_delisted.py);
- every venue market the catalogue lacks, either as a *candidate* that passed every
  gate below, or as *unresolved* with the gate it failed;
- the markets in `scripts/hyperliquid_watch.json`: deliberately unmapped markets whose
  identity is in doubt, each with what was found and what would change the decision.
  A watched market is reported as changed once it trades, its circulating supply
  differs from the recorded one, or its HyperEVM contract gets a nonzero supply.
  `--check-watch` exits 1 on a change (or when the watch could not be read) and
  then ignores flag disagreements, so a scheduled run can fail loudly on the watch
  alone.

    # report only (exit 1 when a flag disagrees)
    PYTHONPATH=lib/src .venv/bin/python scripts/hyperliquid.py

    # also set the delisted flags from isDelisted, then add the candidates
    PYTHONPATH=lib/src .venv/bin/python scripts/hyperliquid.py --write --add
    PYTHONPATH=lib/src .venv/bin/python scripts/instrument_urls.py

`--write` only flips `delisted` (and drops the `url` of a market it delists; run
`instrument_urls.py` afterwards to give a re-listed market its `url` back). It never
adds or removes instruments. `--add` appends the candidates. A catalogue market the
venue no longer returns is reported, not changed.

On HIP-3 dexes `isDelisted: true` also means "registered, not open yet": a deployer
registers a market before it opens, and the flag clears when it opens. So the flags
need re-checking on a schedule (run `--write` daily and open a PR with the flips),
not treating as final.

A missing market is a candidate only when all of these hold; anything else stays for a
person to resolve under AGENTS.md:

1. Its coin (the name after `<dex>:`) is the `symbol` or Yahoo ticker of exactly one
   catalogue asset. No match, or several (TST, CORN), is unresolved.
2. No other Hyperliquid perpetual with that coin maps to a different base. The same
   ticker can be two things on two dexes (STX is Stacks on the main dex and Seagate
   on para), so a clash is unresolved.
3. Its mark price is within `TOLERANCE` of a reference: the asset's Yahoo quote when
   it has a Yahoo ticker, else the mark of a listed Hyperliquid perpetual on the same
   base. No reference is unresolved; this also rejects inverted FX tickers (xyz:JPY
   prints USD/JPY at 158, not the yen's dollar price).
4. The dex's collateral token is in `data/asset_translations/hyperliquid.json`.

Candidates get `quote: tether` (AGENTS.md: Hyperliquid perpetuals are quoted in USDT,
with HYPE and PURR the documented exceptions), `settlement` from the dex collateral,
`exchange` the dex prefix (`""` on the main dex) and `delisted: true` when the venue
says so.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path
import sys
from typing import Callable
import urllib.parse
import urllib.request

from check_hyperliquid_delisted import disagreements, post

ROOT = Path(__file__).resolve().parent.parent
TOLERANCE = 0.03
"""Largest relative gap between the venue mark and the reference price for a candidate."""
QUOTE = 'tether'
YAHOO = 'https://query1.finance.yahoo.com/v8/finance/chart/{}?range=1d&interval=1d'
HYPEREVM = 'https://rpc.hyperliquid.xyz/evm'
WATCH = ROOT / 'scripts/hyperliquid_watch.json'


@dataclass
class Market:
  name: str
  dex: str
  delisted: bool
  mark: float | None
  open_interest: str | None
  volume: str | None
  collateral: int | None


@dataclass
class Report:
  flips: list[str] = field(default_factory=list)
  candidates: dict[str, dict] = field(default_factory=dict)
  evidence: dict[str, str] = field(default_factory=dict)
  unresolved: dict[str, str] = field(default_factory=dict)


def coin(name: str) -> str:
  return name.split(':', 1)[-1]


def number(value: object) -> float | None:
  try:
    result = float(value)  # type: ignore[arg-type]
  except (TypeError, ValueError):
    return None
  return result if result > 0 else None


def fetch() -> dict[str, Market]:
  """Market name -> Market, across every perp dex."""
  dexes = [''] + [dex['name'] for dex in post({'type': 'perpDexs'}) if dex]  # type: ignore[union-attr]
  markets: dict[str, Market] = {}
  for dex in dexes:
    meta, contexts = post({'type': 'metaAndAssetCtxs', 'dex': dex})  # type: ignore[misc]
    for market, context in zip(meta['universe'], contexts):
      markets[market['name']] = Market(
        name=market['name'], dex=dex, delisted=bool(market.get('isDelisted')),
        mark=number(context.get('markPx')), open_interest=context.get('openInterest'),
        volume=context.get('dayNtlVlm'), collateral=meta.get('collateralToken'),
      )
  return markets


def yahoo_price(ticker: str) -> float | None:
  request = urllib.request.Request(YAHOO.format(urllib.parse.quote(ticker)), headers={'User-Agent': 'Mozilla/5.0'})
  try:
    with urllib.request.urlopen(request, timeout=30) as response:
      return number(json.load(response)['chart']['result'][0]['meta'].get('regularMarketPrice'))
  except Exception:
    return None


def load_assets(directory: Path) -> dict[str, dict]:
  assets = {}
  for path in sorted(directory.glob('*.json')):
    asset = json.loads(path.read_text())
    if not asset.get('replaced_by'):
      assets[asset['id']] = asset
  return assets


def assets_by_ticker(assets: dict[str, dict]) -> dict[str, set[str]]:
  """Upper-cased symbol or Yahoo ticker -> asset ids."""
  index: dict[str, set[str]] = {}
  for id, asset in assets.items():
    tickers = {asset['symbol'].upper()}
    yahoo = (asset.get('external') or {}).get('yahoo')
    if yahoo:
      tickers.add(yahoo.upper())
    for ticker in tickers:
      index.setdefault(ticker, set()).add(id)
  return index


def resolve(
  market: Market, catalogue: dict[str, dict], venue: dict[str, Market], assets: dict[str, dict],
  tickers: dict[str, set[str]], collateral: dict[str, str], price: Callable[[str], float | None],
) -> tuple[dict | None, str]:
  """(instrument, evidence) when every gate passes, else (None, reason)."""
  matches = sorted(tickers.get(coin(market.name).upper(), ()))
  if not matches:
    return None, 'no catalogue asset has this symbol or Yahoo ticker'
  if len(matches) > 1:
    return None, f'symbol shared by {", ".join(matches)}'
  base = matches[0]
  peers = {id: instrument for id, instrument in catalogue.items() if coin(id) == coin(market.name)}
  clashes = sorted(id for id, instrument in peers.items() if instrument['base'] != base)
  if clashes:
    others = ', '.join(f"{id} is {catalogue[id]['base']}" for id in clashes)
    return None, f'{base} by symbol, but {others}'
  settlement = collateral.get(str(market.collateral))
  if settlement is None:
    return None, f'collateral token {market.collateral} has no asset translation'
  if market.mark is None:
    return None, f'{base} by symbol, but the venue has no mark price'
  reference, source = None, ''
  yahoo = (assets[base].get('external') or {}).get('yahoo')
  if yahoo:
    reference, source = price(yahoo), f'Yahoo {yahoo}'
  if reference is None:
    for id, instrument in catalogue.items():
      peer = venue.get(id)
      if instrument['base'] == base and peer and not peer.delisted and peer.mark:
        reference, source = peer.mark, f'Hyperliquid {id}'
        break
  if reference is None:
    return None, f'{base} by symbol, but no price reference (no Yahoo ticker or listed Hyperliquid market)'
  gap = abs(market.mark / reference - 1)
  evidence = f'{base}: mark {market.mark:g} vs {source} {reference:g} ({gap:.1%})'
  if gap > TOLERANCE:
    return None, f'{evidence}, beyond {TOLERANCE:.0%}'
  instrument = {'exchange': market.dex, 'base': base, 'quote': QUOTE, 'settlement': settlement}
  if market.delisted:
    instrument['delisted'] = True
  return instrument, evidence


def build_report(
  catalogue: dict[str, dict], venue: dict[str, Market], assets: dict[str, dict],
  collateral: dict[str, str], price: Callable[[str], float | None] = yahoo_price,
) -> Report:
  report = Report()
  report.flips = disagreements(catalogue, {
    name: {'delisted': m.delisted, 'open_interest': m.open_interest, 'volume': m.volume}
    for name, m in venue.items()
  })
  tickers = assets_by_ticker(assets)
  for name, market in venue.items():
    if name in catalogue:
      continue
    instrument, text = resolve(market, catalogue, venue, assets, tickers, collateral, price)
    if instrument is None:
      report.unresolved[name] = text
    else:
      report.candidates[name] = instrument
      report.evidence[name] = text
  return report


def sync_flags(catalogue: dict[str, dict], venue: dict[str, Market]) -> list[str]:
  """Set every catalogue perpetual's `delisted` from the venue; return the ids changed."""
  changed = []
  for id, instrument in catalogue.items():
    market = venue.get(id)
    if market is None or bool(instrument.get('delisted')) == market.delisted:
      continue
    if market.delisted:
      instrument['delisted'] = True
      instrument.pop('url', None)
    else:
      instrument.pop('delisted', None)
    changed.append(id)
  return changed


def spot_contexts() -> dict[str, dict]:
  """Spot coin (`@<index>` or canonical name) -> its asset context."""
  _, contexts = post({'type': 'spotMetaAndAssetCtxs'})  # type: ignore[misc]
  return {context['coin']: context for context in contexts}


def token_details(token_id: str) -> dict:
  return post({'type': 'tokenDetails', 'tokenId': token_id})  # type: ignore[return-value]


def evm_supply(contract: str) -> int:
  """`totalSupply()` of a HyperEVM ERC-20, in its smallest unit."""
  body = {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [{'to': contract, 'data': '0x18160ddd'}, 'latest']}
  request = urllib.request.Request(HYPEREVM, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
  with urllib.request.urlopen(request, timeout=30) as response:
    return int(json.load(response)['result'], 16)


def watch(
  entries: dict[str, dict], contexts: dict[str, dict],
  details: Callable[[str], dict], supply: Callable[[str], int],
) -> dict[str, list[str]]:
  """Watched market -> what changed since it was left unmapped (empty: nothing)."""
  changes: dict[str, list[str]] = {}
  for name, entry in entries.items():
    found = []
    context = contexts.get(entry['coin'])
    if context is None:
      found.append(f'{entry["coin"]} is no longer returned by spotMetaAndAssetCtxs')
    elif number(context.get('dayNtlVlm')):
      found.append(f'traded {context["dayNtlVlm"]} USDC in 24h at mark {context.get("markPx")}')
    circulating = details(entry['token_id']).get('circulatingSupply')
    if number(circulating) != number(entry['circulating_supply']):
      found.append(f'circulating supply {circulating}, recorded {entry["circulating_supply"]}')
    if entry.get('evm_contract') and supply(entry['evm_contract']):
      found.append(f'HyperEVM {entry["evm_contract"]} totalSupply() is now nonzero')
    changes[name] = found
  return changes


def watch_markdown(entries: dict[str, dict], changes: dict[str, list[str]]) -> str:
  lines = ['', '### Watched unmapped markets (scripts/hyperliquid_watch.json)', '']
  for name, found in changes.items():
    if found:
      lines.append(f'- `{name}` **changed**: {"; ".join(found)}. Map it when: {entries[name]["map_when"]}')
    else:
      lines.append(f'- `{name}`: unchanged, stays unmapped.')
  return '\n'.join(lines) + '\n'


def markdown(report: Report, venue: dict[str, Market]) -> str:
  lines = ['### Delisted flags that disagree with `isDelisted`', '']
  lines += [f'- `{line.split(": ", 1)[0]}`: {line.split(": ", 1)[1]}' for line in report.flips] or ['None.']
  lines += ['', f'### Missing markets that pass every gate ({len(report.candidates)})', '']
  lines += [f'- `{name}` -> {report.evidence[name]}' + (' (delisted)' if venue[name].delisted else '')
            for name in report.candidates] or ['None.']
  listed = {name: reason for name, reason in report.unresolved.items() if not venue[name].delisted}
  lines += ['', f'### Missing markets left for a person ({len(report.unresolved)}, {len(listed)} open)', '']
  lines += [f'- `{name}`{"" if name in listed else " (delisted)"}: {reason}' for name, reason in report.unresolved.items()] or ['None.']
  return '\n'.join(lines) + '\n'


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--data', type=Path, default=ROOT / 'data', help='Catalogue data directory.')
  parser.add_argument('--write', action='store_true', help='set delisted flags from isDelisted')
  parser.add_argument('--add', action='store_true', help='append the missing markets that pass every gate')
  parser.add_argument('--markdown', type=Path, help='also write the report as Markdown to this file')
  parser.add_argument('--check-watch', action='store_true',
                      help='exit 1 when a watched market changed or could not be read; the exit status then ignores flag disagreements')
  args = parser.parse_args()

  path = args.data / 'instruments/perpetual/hyperliquid.json'
  catalogue = json.loads(path.read_text())
  collateral = json.loads((args.data / 'asset_translations/hyperliquid.json').read_text())
  venue = fetch()
  report = build_report(catalogue, venue, load_assets(args.data / 'assets'), collateral)

  entries = json.loads(WATCH.read_text())
  try:
    changes = watch(entries, spot_contexts(), token_details, evm_supply)
  except Exception as error:  # a watch outage must not block the flag sync
    changes = {name: [f'could not be read ({error})'] for name in entries}
  text = markdown(report, venue) + watch_markdown(entries, changes)
  print(text, end='')
  if args.markdown:
    args.markdown.write_text(text)

  changed = sync_flags(catalogue, venue) if args.write else []
  if args.add:
    catalogue.update(report.candidates)
  if changed or (args.add and report.candidates):
    path.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + '\n')
    print(f'Wrote {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}: '
          f'{len(changed)} flag(s) changed, {len(report.candidates) if args.add else 0} market(s) added', file=sys.stderr)
  if args.check_watch:
    sys.exit(1 if any(changes.values()) else 0)
  sys.exit(1 if report.flips and not args.write else 0)


if __name__ == '__main__':
  main()
