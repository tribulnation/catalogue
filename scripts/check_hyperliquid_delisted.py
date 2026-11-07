"""Compare Hyperliquid perpetuals' `delisted` flags with the venue's own `isDelisted`.

Hyperliquid's info API (POST https://api.hyperliquid.xyz/info) lists every perp dex
(`perpDexs`) and, per dex, its markets (`metaAndAssetCtxs` with `dex`). A market is
delisted exactly when its `universe[]` entry carries `isDelisted: true`. Zero open
interest or zero 24h volume is not a delisting: HIP-3 deployers register markets
before they open, and a market added in that window has no trades yet. io:NVDA,
io:AAPL, io:CRCL and para:ANTH were marked delisted that way and then traded.

The script is read-only and needs the network, so CI does not run it. It prints
every catalogue perpetual whose flag disagrees with the venue (both directions) and
exits 1 if there are any:

  PYTHONPATH=lib/src .venv/bin/python scripts/check_hyperliquid_delisted.py [--data data]
"""

import argparse
import json
from pathlib import Path
import sys
import urllib.request

INFO = 'https://api.hyperliquid.xyz/info'


def post(body: dict) -> object:
  request = urllib.request.Request(
    INFO, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'},
  )
  with urllib.request.urlopen(request, timeout=30) as response:
    return json.load(response)


def venue_markets() -> dict[str, dict]:
  """Market name -> {'delisted', 'open_interest', 'volume'} across every perp dex."""
  dexes = [''] + [dex['name'] for dex in post({'type': 'perpDexs'}) if dex]  # type: ignore[union-attr]
  markets: dict[str, dict] = {}
  for dex in dexes:
    meta, contexts = post({'type': 'metaAndAssetCtxs', 'dex': dex})  # type: ignore[misc]
    for market, context in zip(meta['universe'], contexts):
      markets[market['name']] = {
        'delisted': bool(market.get('isDelisted')),
        'open_interest': context.get('openInterest'),
        'volume': context.get('dayNtlVlm'),
      }
  return markets


def disagreements(catalogue: dict[str, dict], venue: dict[str, dict]) -> list[str]:
  """One line per catalogue instrument whose `delisted` flag the venue contradicts."""
  lines = []
  for id, instrument in catalogue.items():
    market = venue.get(id)
    if market is None:
      if not instrument.get('delisted'):
        lines.append(f'{id}: listed in the catalogue, not returned by the venue')
      continue
    if bool(instrument.get('delisted')) != market['delisted']:
      state = 'delisted' if market['delisted'] else 'listed'
      lines.append(
        f'{id}: catalogue delisted={bool(instrument.get("delisted"))}, venue {state} '
        f'(open interest {market["open_interest"]}, 24h volume {market["volume"]})'
      )
  return lines


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--data', default='data', help='Catalogue data directory.')
  args = parser.parse_args()
  catalogue = json.loads((Path(args.data) / 'instruments/perpetual/hyperliquid.json').read_text())
  lines = disagreements(catalogue, venue_markets())
  for line in lines:
    print(line)
  print(f'{len(lines)} Hyperliquid perpetual(s) disagree with the venue', file=sys.stderr)
  sys.exit(1 if lines else 0)


if __name__ == '__main__':
  main()
