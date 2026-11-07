"""Fail when a Lighter or Hyperliquid perpetual is quoted in its settlement coin, USDC.

A perpetual's `quote` is the currency its index price tracks; `settlement` is what it
pays out in (AGENTS.md, "Perpetual quote is the index currency"). On these platforms
the two differ: every perpetual settles in USDC (or a HIP-3 dex's own collateral),
while the index is USDT for crypto and USD for stocks, ETFs, commodities, FX and
pre-IPO markets. `quote: usd-coin` there is almost always the settlement coin copied
into the quote, and it makes consumers price the market against USDC.

So a perpetual on a platform in `PLATFORMS` with `quote: usd-coin` fails, unless
`scripts/perp_quote_exceptions.json` lists it (`"<platform>:<instrument id>"`) with the
evidence that its index really is USDC. An exception whose instrument is gone or no
longer quoted in USDC fails too, so the list cannot go stale.

  PYTHONPATH=lib/src .venv/bin/python scripts/check_perp_quotes.py [--data data]
"""

import argparse
import json
from pathlib import Path
import sys

PLATFORMS = ('lighter', 'hyperliquid')
"""Platforms whose perpetuals' index is never their USDC settlement."""
USDC = 'usd-coin'
EXCEPTIONS = Path(__file__).with_name('perp_quote_exceptions.json')
HINT = {
  'crypto': 'tether',
}
"""Asset category -> the usual index quote on these platforms (else `usd`)."""


def load_exceptions(path: Path = EXCEPTIONS) -> dict[str, str]:
  """`"<platform>:<id>"` -> the reason its index is USDC (keys starting with `_` are notes)."""
  raw = json.loads(path.read_text())
  return {k: v for k, v in raw.items() if not k.startswith('_')}


def category(data: Path, asset: str) -> str | None:
  """An asset's category, if its record exists."""
  try:
    return json.loads((data / 'assets' / f'{asset}.json').read_text()).get('category')
  except (OSError, ValueError):
    return None


def errors(data: Path, exceptions: dict[str, str]) -> list[str]:
  """Every USDC-quoted perpetual not excepted, and every stale or unexplained exception."""
  out = []
  seen = set()
  for platform in PLATFORMS:
    path = data / 'instruments' / 'perpetual' / f'{platform}.json'
    if not path.exists():
      continue
    for id, inst in json.loads(path.read_text()).items():
      if inst.get('quote') != USDC:
        continue
      key = f'{platform}:{id}'
      seen.add(key)
      if key in exceptions:
        continue
      base = inst.get('base')
      want = HINT.get(category(data, base) or '', 'usd')
      out.append(
        f'{key} ({base}): quote is {USDC}, its settlement coin; set the currency its '
        f'index tracks (usually "{want}" for a {category(data, base) or "?"} asset), or '
        f'add "{key}" to {EXCEPTIONS.name} with the evidence that the index is USDC'
      )
  for key, reason in sorted(exceptions.items()):
    if key not in seen:
      out.append(f'{EXCEPTIONS.name}: {key} is not a {USDC}-quoted perpetual any more; remove it')
    elif not str(reason).strip():
      out.append(f'{EXCEPTIONS.name}: {key} has no reason')
  return out


def main(argv: list[str] | None = None) -> int:
  """CLI entry point."""
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  parser.add_argument('--data', type=Path, default=Path('data'))
  parser.add_argument('--exceptions', type=Path, default=EXCEPTIONS)
  args = parser.parse_args(argv)
  found = errors(args.data, load_exceptions(args.exceptions))
  for line in found:
    print(line, file=sys.stderr)
  if not found:
    print(f'No {USDC}-quoted perpetuals on {", ".join(PLATFORMS)} beyond the listed exceptions.')
  return 1 if found else 0


if __name__ == '__main__':
  sys.exit(main())
