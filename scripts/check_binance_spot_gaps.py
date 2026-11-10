"""List Binance spot markets the catalogue could carry but does not.

A market is a gap when Binance reports it `TRADING`, both its base and quote
assets are already in `data/asset_translations/binance.json`, and its symbol is
missing from `data/instruments/spot/binance.json`. Such a market needs no new
asset or translation, only an instrument entry, so it tends to go unnoticed
until a portfolio holds it: SKUUBUSDT (#395) and GEVBUSDT (#402) were found that
way.

The script is read-only and needs the network, so CI does not run it. It reads
`GET /api/v3/exchangeInfo` and `GET /api/v3/ticker/24hr` from Binance's public
API, prints one line per gap (largest 24h quote volume first) and exits 1 if
there are any:

  PYTHONPATH=lib/src .venv/bin/python scripts/check_binance_spot_gaps.py [--data data]

Binance blocks some cloud regions; run it from somewhere that can reach
api.binance.com. Verify each gap (price against the underlying, the asset's
identity) before adding it, and run `scripts/instrument_urls.py` afterwards.
"""

import argparse
import json
from pathlib import Path
import sys
import urllib.request

from maintenance import generators
from maintenance.finding import make, market_subject

API = 'https://api.binance.com/api/v3'


def get(path: str) -> object:
  with urllib.request.urlopen(f'{API}/{path}', timeout=30) as response:
    return json.load(response)


def gaps(
  symbols: list[dict], translations: dict[str, str], catalogue: dict[str, dict],
  volumes: dict[str, str] | None = None,
) -> list[str]:
  """One line per trading symbol whose base and quote are translated but which has no instrument."""
  volumes = volumes or {}
  found = []
  for market in symbols:
    symbol = market['symbol']
    if market.get('status') != 'TRADING' or symbol in catalogue:
      continue
    base, quote = translations.get(market['baseAsset']), translations.get(market['quoteAsset'])
    if base is None or quote is None:
      continue
    volume = volumes.get(symbol)
    found.append((float(volume or 0), f'{symbol}: base {base}, quote {quote}, 24h quote volume {volume}'))
  found.sort(key=lambda item: -item[0])
  return [line for _, line in found]


USD_QUOTES = {'USDT', 'USDC', 'FDUSD', 'USD1', 'TUSD', 'USDP', 'BUSD'}
"""Quote assets whose 24h quote volume is close enough to USD to rank a gap."""


def findings(
  symbols: list[dict], translations: dict[str, str], catalogue: dict[str, dict],
  volumes: dict[str, str] | None = None,
) -> list[dict]:
  """The gaps as `untranslated-market` findings (`--report-json`), with the instrument to add.

  Medium from 100k USD of 24h quote volume on a dollar-quoted market, else low.
  """
  volumes = volumes or {}
  out = []
  for market in symbols:
    symbol = market['symbol']
    if market.get('status') != 'TRADING' or symbol in catalogue:
      continue
    base, quote = translations.get(market['baseAsset']), translations.get(market['quoteAsset'])
    if base is None or quote is None:
      continue
    volume = float(volumes.get(symbol) or 0) if market['quoteAsset'] in USD_QUOTES else None
    severity = 'medium' if volume is not None and volume >= generators.MIN_VOLUME_USD else 'low'
    subject = market_subject('spot', symbol)
    out.append(make(
      'untranslated-market', platform='binance', subject=subject, severity=severity,
      summary=f'binance spot market {subject} is not in the catalogue',
      evidence={
        'exchange': 'spot', 'market': symbol, 'kind': 'spot',
        'venue_pair': {'base': market['baseAsset'], 'quote': market['quoteAsset'], 'settlement': None},
        'usd_volume_24h': volume,
        'draft': {
          'file': 'data/instruments/spot/binance.json', 'id': symbol,
          'add': {'exchange': 'spot', 'base': base, 'quote': quote},
        },
      },
    ))
  return out


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--data', default='data', help='Catalogue data directory.')
  parser.add_argument('--report-json', type=Path, help='Also write the gaps as maintenance findings (JSON) here.')
  args = parser.parse_args()
  data = Path(args.data)
  translations = json.loads((data / 'asset_translations/binance.json').read_text())
  catalogue = json.loads((data / 'instruments/spot/binance.json').read_text())
  symbols = get('exchangeInfo')['symbols']  # type: ignore[index]
  volumes = {ticker['symbol']: ticker['quoteVolume'] for ticker in get('ticker/24hr')}  # type: ignore[union-attr]
  lines = gaps(symbols, translations, catalogue, volumes)
  if args.report_json:
    generators.write(args.report_json, 'scripts/check_binance_spot_gaps.py', ['binance'], ['untranslated-market'], findings(symbols, translations, catalogue, volumes))
  for line in lines:
    print(line)
  print(f'{len(lines)} trading Binance spot market(s) with translated assets but no instrument', file=sys.stderr)
  sys.exit(1 if lines else 0)


if __name__ == '__main__':
  main()
