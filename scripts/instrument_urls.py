#!/usr/bin/env python3
"""Fill in the `url` field of spot and perpetual instruments.

Each supported platform has a rule that builds the trading page URL from the
instrument ID (and, where the platform's URLs are split by asset, from the
base/quote symbols parsed out of the ID). Run it after adding instruments:

    PYTHONPATH=lib/src .venv/bin/python scripts/instrument_urls.py

Existing URLs are kept as-is unless `--overwrite` is passed, so hand-written
URLs survive a regeneration.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Callable, Mapping

Instrument = Mapping[str, object]

# Kraken lists bitcoin as XBT and dogecoin as XDG, but its trading pages use BTC/DOGE.
_KRAKEN_SYMBOLS = {'XBT': 'BTC', 'XDG': 'DOGE'}

_HYPERLIQUID_SPOT_INDEX = re.compile(r':\d+$')


class Symbols:
  """Platform-native asset symbols, used to split concatenated instrument IDs."""

  def __init__(self, data: Path):
    self.assets = {
      file.stem: json.loads(file.read_text())
      for file in (data / 'assets').glob('*.json')
    }
    self.translations: dict[str, dict[str, set[str]]] = {}
    for file in (data / 'asset_translations').glob('*.json'):
      platform: dict[str, set[str]] = {}
      for symbol, asset in json.loads(file.read_text()).items():
        platform.setdefault(asset, set()).add(symbol)
      self.translations[file.stem] = platform

  def candidates(self, platform: str, asset: str) -> set[str]:
    symbols = set(self.translations.get(platform, {}).get(asset, ()))
    if (catalogue_symbol := self.assets.get(asset, {}).get('symbol')) is not None:
      symbols.add(catalogue_symbol)
    if asset == 'bitcoin':
      symbols.add('XBT')
    return symbols

  def split(self, platform: str, id: str, instrument: Instrument) -> tuple[str, str]:
    """Split a concatenated ID (e.g. `1INCHUSDT`) into its base and quote symbols.

    Several quote symbols can match as a suffix (Kraken knows bitcoin as both
    `XBT` and `XXBT`, so `SNXXBT` splits as either `SNX`/`XBT` or `SN`/`XXBT`),
    so a split whose remainder is a known base symbol wins over a longer one.
    """
    bases = {b.upper() for b in self.candidates(platform, str(instrument['base']))}
    quotes = self.candidates(platform, str(instrument['quote']))
    matches = [q for q in quotes if len(id) > len(q) and id.upper().endswith(q.upper())]
    if not matches:
      raise ValueError(f'Cannot split "{id}" on "{platform}": no quote symbol in {sorted(quotes)}')
    quote = max(matches, key=lambda q: (id[: len(id) - len(q)].upper() in bases, len(q)))
    return id[: len(id) - len(quote)], id[len(id) - len(quote) :]


def _kraken_symbol(symbol: str) -> str:
  return _KRAKEN_SYMBOLS.get(symbol.upper(), symbol.upper()).lower()


def _bitget_margin(instrument: Instrument) -> str:
  if str(instrument['settlement']) == 'usd-coin':
    return 'usdc'
  if str(instrument['settlement']) == 'tether':
    return 'usdt'
  return 'coin'


Rule = Callable[[str, Instrument, Symbols], str]

SPOT_RULES: dict[str, Rule] = {
  'binance': lambda id, inst, sym: 'https://www.binance.com/en/trade/{}_{}'.format(*sym.split('binance', id, inst)),
  'bitget': lambda id, inst, sym: f'https://www.bitget.com/spot/{id}',
  'bybit': lambda id, inst, sym: 'https://www.bybit.com/en/trade/spot/{}/{}'.format(*sym.split('bybit', id, inst)),
  'coinbase': lambda id, inst, sym: f'https://www.coinbase.com/advanced-trade/spot/{id}',
  'hyperliquid': lambda id, inst, sym: f'https://app.hyperliquid.xyz/trade/{_HYPERLIQUID_SPOT_INDEX.sub("", id)}',
  'kraken': lambda id, inst, sym: 'https://pro.kraken.com/app/trade/{}-{}'.format(
    *(_kraken_symbol(s) for s in sym.split('kraken', id, inst))
  ),
  'kucoin': lambda id, inst, sym: f'https://www.kucoin.com/trade/{id}',
  'mexc': lambda id, inst, sym: 'https://www.mexc.com/exchange/{}_{}'.format(*sym.split('mexc', id, inst)),
  'okx': lambda id, inst, sym: f'https://www.okx.com/trade-spot/{id.lower()}',
}

PERPETUAL_RULES: dict[str, Rule] = {
  'binance': lambda id, inst, sym: f'https://www.binance.com/en/futures/{id}',
  'bitget': lambda id, inst, sym: f'https://www.bitget.com/futures/{_bitget_margin(inst)}/{id}',
  'bybit': lambda id, inst, sym: f'https://www.bybit.com/trade/usdt/{id}',
  'coinbase': lambda id, inst, sym: f'https://www.coinbase.com/advanced-trade/perpetuals/{id}',
  'dydx': lambda id, inst, sym: f'https://dydx.trade/trade/{id}',
  'hyperliquid': lambda id, inst, sym: f'https://app.hyperliquid.xyz/trade/{id}',
  'kraken': lambda id, inst, sym: f'https://futures.kraken.com/trade/futures/{id}',
  'kucoin': lambda id, inst, sym: f'https://www.kucoin.com/trade/futures/{id}',
  'mexc': lambda id, inst, sym: f'https://www.mexc.com/futures/{id}',
  'okx': lambda id, inst, sym: f'https://www.okx.com/trade-swap/{id.lower()}',
}

RULES = {'spot': SPOT_RULES, 'perpetual': PERPETUAL_RULES}


def fill(folder: Path, rules: dict[str, Rule], symbols: Symbols, *, overwrite: bool) -> tuple[int, int]:
  """Write URLs into every instrument file in `folder`. Returns (filled, skipped)."""
  filled = skipped = 0
  for file in sorted(folder.glob('*.json')):
    rule = rules.get(file.stem)
    instruments: dict[str, dict] = json.loads(file.read_text())
    if rule is None:
      skipped += len(instruments)
      continue
    for id, instrument in instruments.items():
      if 'url' in instrument and not overwrite:
        continue
      instrument['url'] = rule(id, instrument, symbols)
      filled += 1
    file.write_text(json.dumps(instruments, ensure_ascii=False, indent=2) + '\n')
  return filled, skipped


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--data', default='data', help='Catalogue data directory.')
  parser.add_argument('--overwrite', action='store_true', help='Replace existing URLs.')
  args = parser.parse_args()

  data = Path(args.data)
  symbols = Symbols(data)
  for kind, rules in RULES.items():
    filled, skipped = fill(data / 'instruments' / kind, rules, symbols, overwrite=args.overwrite)
    print(f'{kind}: {filled} URLs written' + (f', {skipped} on platforms without a rule' if skipped else ''))


if __name__ == '__main__':
  main()
