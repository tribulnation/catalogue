"""Check `asset.external` provider IDs against the providers themselves.

`scripts/validate.py` is offline: it can tell that an external ID is
well-formed, but not that it points at the asset the catalogue thinks it does.
This script closes that gap by resolving every CoinGecko and CoinMarketCap ID
against the provider and reporting three distinct outcomes:

  unresolved  the provider does not know the ID at all — a dead or mistyped
              listing, so any price lookup for that asset fails outright
  mismatch    the ID resolves, but to a token whose symbol does not match the
              catalogue's — the dangerous case, because prices still come back,
              just for the wrong token
  ok          the ID resolves to a matching symbol

A mismatch is not automatically an error. Providers rename entries in place
(a rebrand keeps the ID) and the catalogue deliberately uses an underlying
asset's ID for some wrappers. So mismatches are reported for a human to judge,
never auto-corrected. Once judged benign, a mismatch is recorded in
`scripts/external_id_exceptions.json` with the reason, which keeps the output
down to what has not been looked at yet. An exception is keyed by the exact
mapping it was granted for, so repointing an asset at a new ID re-reports it.

Network access is required; this is not part of CI validation.

Usage:
  PYTHONPATH=lib/src .venv/bin/python scripts/check_external_ids.py
  PYTHONPATH=lib/src .venv/bin/python scripts/check_external_ids.py --provider coingecko
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

COINGECKO_LIST = 'https://api.coingecko.com/api/v3/coins/list'
COINGECKO_CURRENCIES = 'https://api.coingecko.com/api/v3/simple/supported_vs_currencies'
COINMARKETCAP_QUOTES = 'https://api.coinmarketcap.com/data-api/v3/cryptocurrency/quote/latest?id='

# CoinMarketCap's web endpoint takes a comma-separated id list; keep batches
# small enough to stay well inside its URL and rate limits.
CMC_BATCH = 100

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64)'


@dataclass
class Finding:
  kind: str  # 'unresolved' | 'mismatch'
  provider: str
  asset: str
  symbol: str
  external_id: str
  found: str = ''

  def __str__(self) -> str:
    where = f'{self.asset} ({self.symbol}) -> {self.provider}:{self.external_id}'
    if self.kind == 'unresolved':
      return f'unresolved: {where} is unknown to {self.provider}'
    return f'mismatch:   {where} resolves to {self.found}'


def fetch(url: str, *, tries: int = 6) -> dict | list:
  """GET `url` as JSON, backing off on rate limits and transient 5xx."""
  delay = 3.0
  last: Exception | None = None
  for _ in range(tries):
    try:
      request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
      with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
      if e.code not in (429, 500, 502, 503, 504):
        raise
      last = e
    except Exception as e:  # noqa: BLE001 - transport errors are all retryable
      last = e
    time.sleep(delay)
    delay = min(delay * 2, 60)
  assert last is not None
  raise last


def load_assets(data: Path) -> list[dict]:
  return [json.loads(file.read_text()) for file in sorted((data / 'assets').glob('*.json'))]


def check_coingecko(assets: list[dict]) -> list[Finding]:
  """Resolve CoinGecko IDs against the full coin list.

  One request covers every asset, so this is cheap regardless of catalogue
  size. `currency:` IDs are fiat quotes rather than coins and are checked
  against the supported-currency list instead.
  """
  coins = fetch(COINGECKO_LIST)
  assert isinstance(coins, list)
  by_id = {coin['id']: coin for coin in coins}
  currencies = set(fetch(COINGECKO_CURRENCIES))  # type: ignore[arg-type]

  findings: list[Finding] = []
  for asset in assets:
    external_id = asset.get('external', {}).get('coingecko')
    if not external_id:
      continue
    if external_id.startswith('currency:'):
      if external_id.removeprefix('currency:') not in currencies:
        findings.append(Finding('unresolved', 'coingecko', asset['id'], asset['symbol'], external_id))
      continue
    coin = by_id.get(external_id)
    if coin is None:
      findings.append(Finding('unresolved', 'coingecko', asset['id'], asset['symbol'], external_id))
    elif coin['symbol'].upper() != asset['symbol'].upper():
      findings.append(Finding(
        'mismatch', 'coingecko', asset['id'], asset['symbol'], external_id,
        found=f"{coin['symbol'].upper()} ({coin['name']})",
      ))
  return findings


def check_coinmarketcap(assets: list[dict]) -> list[Finding]:
  """Resolve CoinMarketCap numeric IDs in batches."""
  wanted = {
    asset['external']['coinmarketcap']: asset
    for asset in assets
    if asset.get('external', {}).get('coinmarketcap')
  }
  ids = sorted(wanted, key=int)

  resolved: dict[str, dict] = {}
  for start in range(0, len(ids), CMC_BATCH):
    batch = ids[start:start + CMC_BATCH]
    response = fetch(COINMARKETCAP_QUOTES + ','.join(batch))
    assert isinstance(response, dict)
    for entry in response.get('data') or []:
      resolved[str(entry['id'])] = entry

  findings: list[Finding] = []
  for external_id in ids:
    asset = wanted[external_id]
    entry = resolved.get(external_id)
    if entry is None:
      findings.append(Finding('unresolved', 'coinmarketcap', asset['id'], asset['symbol'], external_id))
    elif entry['symbol'].upper() != asset['symbol'].upper():
      findings.append(Finding(
        'mismatch', 'coinmarketcap', asset['id'], asset['symbol'], external_id,
        found=f"{entry['symbol'].upper()} ({entry['name']})",
      ))
  return findings


CHECKS = {'coingecko': check_coingecko, 'coinmarketcap': check_coinmarketcap}

EXCEPTIONS_FILE = Path(__file__).parent / 'external_id_exceptions.json'


def load_exceptions(file: Path) -> dict[str, str]:
  """Reviewed-and-accepted mismatches, keyed '<asset>:<provider>:<external_id>'."""
  if not file.exists():
    return {}
  return {
    key: reason for key, reason in json.loads(file.read_text()).items()
    if not key.startswith('_')
  }


def key_of(finding: Finding) -> str:
  return f'{finding.asset}:{finding.provider}:{finding.external_id}'


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--data', type=Path, default=Path('data'), help='Catalogue data folder.')
  parser.add_argument('--provider', choices=sorted(CHECKS), action='append',
                      help='Only check this provider. Repeatable; defaults to all.')
  parser.add_argument('--strict', action='store_true',
                      help='Also exit non-zero on mismatches, which normally need a human call.')
  parser.add_argument('--all', action='store_true',
                      help='Also show mismatches already reviewed and recorded as exceptions.')
  args = parser.parse_args()

  assets = load_assets(args.data)
  providers = args.provider or sorted(CHECKS)
  exceptions = load_exceptions(EXCEPTIONS_FILE)

  findings: list[Finding] = []
  for provider in providers:
    findings += CHECKS[provider](assets)

  unresolved = [f for f in findings if f.kind == 'unresolved']
  mismatches = [f for f in findings if f.kind == 'mismatch' and key_of(f) not in exceptions]
  accepted = [f for f in findings if f.kind == 'mismatch' and key_of(f) in exceptions]

  for finding in sorted(unresolved + mismatches, key=lambda f: (f.kind, f.provider, f.asset)):
    print(finding, file=sys.stderr)
  if args.all:
    for finding in sorted(accepted, key=lambda f: (f.provider, f.asset)):
      print(f'accepted:   {finding} - {exceptions[key_of(finding)]}', file=sys.stderr)

  checked = sum(1 for a in assets for p in providers if a.get('external', {}).get(p))
  print(f'Checked {checked} external IDs across {", ".join(providers)}.')
  print(f'> Unresolved: {len(unresolved)}')
  print(f'> Mismatched: {len(mismatches)} (review by hand; renames keep the provider ID)')
  print(f'> Accepted:   {len(accepted)} (reviewed, see {EXCEPTIONS_FILE.name})')

  stale = sorted(set(exceptions) - {key_of(f) for f in accepted})
  if stale:
    print(f'> Stale exceptions no longer matching any mismatch: {len(stale)}')
    for key in stale:
      print(f'  {key}', file=sys.stderr)

  if unresolved or (args.strict and mismatches):
    return 1
  return 0


if __name__ == '__main__':
  raise SystemExit(main())
