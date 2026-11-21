#!/usr/bin/env python3
"""Sync `data/instruments/margin/bitget.json` with Bitget's spot margin pairs.

Bitget's Unified Trading Account lists its margin pairs at
GET https://api.bitget.com/api/v3/market/instruments?category=MARGIN (public, no key).
A margin pair trades the spot book of the same symbol on borrowed funds, so each one is
recorded with the base and quote of that spot pair and `exchange` `margin` (the SDK's
`<account>:margin:<SYMBOL>` market).

    # report only (exit 1 when the file would change)
    PYTHONPATH=lib/src .venv/bin/python scripts/bitget_margin.py

    # apply: add candidates, flip `delisted` flags
    PYTHONPATH=lib/src .venv/bin/python scripts/bitget_margin.py --write

A venue pair is a candidate only when all of these hold; the rest are reported with the
gate they failed:

1. `status` is `online` and `instrumentType` is `crypto` (stock, ETF and metal tokens are skipped).
2. Its `baseCoin` and `quoteCoin` have Bitget asset translations (`data/asset_translations/bitget.json`),
   the same mapping the Bitget spot pairs use. Bitget's `r`-prefixed stock tokens report
   `instrumentType` `crypto` but are untranslated by design, so they stop here.
3. The same symbol is a listed Bitget spot pair with that base and quote.

A catalogued margin pair the venue no longer lists as online is marked `delisted`; one that
comes back loses the flag. Pairs are never removed.
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path

from typing_extensions import Any, Literal, TypedDict

URL = 'https://api.bitget.com/api/v3/market/instruments?category=MARGIN'
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
EXCHANGE = 'margin'

Gate = Literal['not-online', 'not-crypto', 'untranslated', 'no-spot-pair']


class VenuePair(TypedDict):
  """The fields of one `category=MARGIN` instrument this script reads."""
  symbol: str
  baseCoin: str
  quoteCoin: str
  status: str
  instrumentType: str


class Plan(TypedDict):
  """What `--write` would do, and why the remaining venue pairs were left out."""
  instruments: dict[str, dict[str, Any]]
  """The resulting margin instruments, keyed by symbol"""
  added: list[str]
  delisted: list[str]
  relisted: list[str]
  skipped: dict[str, Gate]
  """Venue symbol -> first gate it failed"""


def gate(pair: VenuePair, *, translations: dict[str, str], spot: dict[str, dict[str, Any]]) -> Gate | None:
  """The first gate `pair` fails, or None when it can be catalogued."""
  if pair['status'] != 'online':
    return 'not-online'
  elif pair['instrumentType'] != 'crypto':
    return 'not-crypto'
  elif pair['baseCoin'] not in translations or pair['quoteCoin'] not in translations:
    return 'untranslated'
  elif not spot_matches(spot.get(pair['symbol']), base=translations[pair['baseCoin']], quote=translations[pair['quoteCoin']]):
    return 'no-spot-pair'


def spot_matches(instrument: dict[str, Any] | None, *, base: str, quote: str) -> bool:
  """Whether a spot instrument is listed and trades `base` against `quote`."""
  return instrument is not None and not instrument.get('delisted') and instrument['base'] == base and instrument['quote'] == quote


def plan(
  pairs: list[VenuePair], *, translations: dict[str, str], spot: dict[str, dict[str, Any]], existing: dict[str, dict[str, Any]],
) -> Plan:
  """Merge the venue's margin pairs into the catalogued ones.

  Args:
    pairs: The venue's `category=MARGIN` instruments.
    translations: Bitget asset translations (venue coin -> asset id).
    spot: Catalogued Bitget spot instruments.
    existing: Catalogued Bitget margin instruments.
  """
  instruments = {id: dict(instrument) for id, instrument in existing.items()}
  added: list[str] = []
  skipped: dict[str, Gate] = {}
  listed: set[str] = set()
  for pair in pairs:
    symbol = pair['symbol']
    if (failed := gate(pair, translations=translations, spot=spot)) is not None:
      skipped[symbol] = failed
    else:
      listed.add(symbol)
      if symbol not in instruments:
        instruments[symbol] = {'exchange': EXCHANGE, 'base': translations[pair['baseCoin']], 'quote': translations[pair['quoteCoin']]}
        added.append(symbol)
  delisted = sorted(id for id, instrument in instruments.items() if id not in listed and not instrument.get('delisted'))
  relisted = sorted(id for id, instrument in instruments.items() if id in listed and instrument.get('delisted'))
  for id in delisted:
    instruments[id]['delisted'] = True
    instruments[id].pop('url', None)
  for id in relisted:
    del instruments[id]['delisted']
  return Plan(
    instruments=dict(sorted(instruments.items())), added=sorted(added), delisted=delisted, relisted=relisted,
    skipped=dict(sorted(skipped.items())),
  )


def fetch() -> list[VenuePair]:
  """Bitget's margin pairs from the public v3 endpoint."""
  request = urllib.request.Request(URL, headers={'User-Agent': 'catalogue-sync'})
  with urllib.request.urlopen(request, timeout=30) as response:
    body = json.load(response)
  if body.get('code') != '00000':
    raise RuntimeError(f'Bitget answered {body.get("code")}: {body.get("msg")}')
  return body['data']


def read(path: Path) -> dict[str, Any]:
  """A JSON object file, or `{}` when it does not exist."""
  return json.loads(path.read_text()) if path.exists() else {}


def main():
  """Report (and with `--write`, apply) the differences with the venue."""
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--write', action='store_true', help='Write the margin instruments file')
  args = parser.parse_args()

  path = DATA / 'instruments' / 'margin' / 'bitget.json'
  result = plan(
    fetch(),
    translations=read(DATA / 'asset_translations' / 'bitget.json'),
    spot=read(DATA / 'instruments' / 'spot' / 'bitget.json'),
    existing=read(path),
  )
  for label in ('added', 'delisted', 'relisted'):
    print(f'{label}: {len(result[label])} {" ".join(result[label])}')
  by_gate: dict[str, list[str]] = {}
  for symbol, failed in result['skipped'].items():
    by_gate.setdefault(failed, []).append(symbol)
  for failed, symbols in sorted(by_gate.items()):
    print(f'skipped ({failed}): {len(symbols)} {" ".join(symbols)}')

  changed = bool(result['added'] or result['delisted'] or result['relisted'])
  if args.write and changed:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result['instruments'], indent=2, ensure_ascii=False) + '\n')
    print(f'wrote {path.relative_to(ROOT)} ({len(result["instruments"])} instruments)')
  elif changed:
    sys.exit(1)


if __name__ == '__main__':
  main()
