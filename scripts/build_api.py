#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from html import escape
from urllib.parse import quote, urljoin

from tribulnation.catalogue import load, validate
from tribulnation.catalogue.schema import Catalogue


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description='Build the static catalogue API.')
  parser.add_argument('--data', default='data', help='Catalogue data directory.')
  parser.add_argument(
    '--output',
    help='Static asset output directory. Defaults to app/static when app/ exists, otherwise public.',
  )
  parser.add_argument('--public-url', help='Optional public base URL for generated absolute asset URLs.')
  return parser.parse_args()


def json_default(value: Any):
  if isinstance(value, datetime):
    return value.isoformat()
  if isinstance(value, date):
    return value.isoformat()
  if isinstance(value, Decimal):
    return str(value)
  if is_dataclass(value):
    return asdict(value)
  raise TypeError(f'Object of type {type(value).__name__} is not JSON serializable')


def write_json(path: Path, data: Any):
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(
    json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, default=json_default) + '\n'
  )


def clean_public_url(public_url: str | None) -> str | None:
  if public_url is None:
    return None
  return public_url.rstrip('/') + '/'


def public_path(public_url: str | None, path: str) -> str:
  if public_url is None:
    return '/' + path.lstrip('/')
  return urljoin(public_url, path.lstrip('/'))


def with_id(id: str, item: dict[str, Any], public_url: str | None) -> dict[str, Any]:
  out = {'id': id, **deepcopy(item)}
  if icon := out.get('icon'):
    out['icon'] = public_path(public_url, icon)
  return out


def asset_summary(id: str, asset: dict[str, Any], public_url: str | None) -> dict[str, Any]:
  out: dict[str, Any] = {
    'id': id,
    'display_name': asset['display_name'],
    'symbol': asset['symbol'],
  }
  for field in ('icon', 'tags', 'pegged_to'):
    if field in asset:
      out[field] = deepcopy(asset[field])
  if icon := out.get('icon'):
    out['icon'] = public_path(public_url, icon)
  return out


def localized_asset(id: str, asset: dict[str, Any], public_url: str | None, locale: str, about: str) -> dict[str, Any]:
  out = with_id(id, asset, public_url)
  out['locale'] = locale
  out['about'] = about
  return out


def platform_summary(id: str, platform: dict[str, Any], public_url: str | None, *, blockchain: bool = False) -> dict[str, Any]:
  out: dict[str, Any] = {
    'id': id,
    'display_name': platform['display_name'],
    'kind': platform['kind'],
  }
  fields = ('icon', 'native_asset', 'category', 'namespace', 'chain_id') if blockchain else ('icon',)
  for field in fields:
    if field in platform:
      out[field] = deepcopy(platform[field])
  if icon := out.get('icon'):
    out['icon'] = public_path(public_url, icon)
  return out


def keyed_records(items: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
  return {
    id: {'id': id, **deepcopy(item)}
    for id, item in sorted(items.items())
  }


def write_platform_maps(base: Path, maps: dict[str, dict[str, Any]]):
  for platform, items in sorted(maps.items()):
    write_json(base / f'{platform}.json', keyed_records(items))


def platform_index(maps: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
  return [
    {'platform': platform, 'count': len(items)}
    for platform, items in sorted(maps.items())
  ]


def add_ref(index: dict[str, list[dict[str, str]]], asset: str, ref: dict[str, str]):
  index.setdefault(asset, []).append(ref)


def instrument_index(catalogue: Catalogue) -> dict[str, list[dict[str, str]]]:
  index: dict[str, list[dict[str, str]]] = {}

  for platform, instruments in catalogue.spot_instruments.items():
    for id, instrument in instruments.items():
      add_ref(index, instrument['base'], {'kind': 'spot', 'platform': platform, 'id': id, 'role': 'base'})
      add_ref(index, instrument['quote'], {'kind': 'spot', 'platform': platform, 'id': id, 'role': 'quote'})

  for platform, instruments in catalogue.perpetual_instruments.items():
    for id, instrument in instruments.items():
      add_ref(index, instrument['base'], {'kind': 'perpetual', 'platform': platform, 'id': id, 'role': 'base'})
      add_ref(index, instrument['quote'], {'kind': 'perpetual', 'platform': platform, 'id': id, 'role': 'quote'})
      add_ref(index, instrument['settlement'], {'kind': 'perpetual', 'platform': platform, 'id': id, 'role': 'settlement'})

  for platform, instruments in catalogue.debt_instruments.items():
    for id, instrument in instruments.items():
      add_ref(index, instrument['asset'], {'kind': 'debt', 'platform': platform, 'id': id, 'role': 'asset'})

  for platform, instruments in catalogue.collateral_instruments.items():
    for id, instrument in instruments.items():
      add_ref(index, instrument['asset'], {'kind': 'collateral', 'platform': platform, 'id': id, 'role': 'asset'})

  for platform, instruments in catalogue.pools.items():
    for id, instrument in instruments.items():
      for asset in instrument['assets']:
        add_ref(index, asset, {'kind': 'pool', 'platform': platform, 'id': id, 'role': 'asset'})

  return {
    asset: sorted(refs, key=lambda ref: (ref['kind'], ref['platform'], ref['id'], ref['role']))
    for asset, refs in sorted(index.items())
  }


def symbols_index(catalogue: Catalogue) -> dict[str, list[str]]:
  out: dict[str, list[str]] = {}
  for id, asset in catalogue.assets.items():
    out.setdefault(asset['symbol'], []).append(id)
  return {symbol: sorted(ids) for symbol, ids in sorted(out.items())}


def external_index(catalogue: Catalogue, provider: str) -> dict[str, str]:
  out: dict[str, str] = {}
  for id, asset in sorted(catalogue.assets.items()):
    external = asset.get('external', {})
    if provider_id := external.get(provider):
      if provider_id in out:
        raise ValueError(f'Duplicate {provider} id "{provider_id}" for "{out[provider_id]}" and "{id}"')
      out[provider_id] = id
  return out


def pegs_index(catalogue: Catalogue) -> dict[str, list[str]]:
  out: dict[str, list[str]] = {}
  for id, asset in catalogue.assets.items():
    if peg := asset.get('pegged_to'):
      out.setdefault(peg['asset'], []).append(id)
  return {asset: sorted(ids) for asset, ids in sorted(out.items())}


def stats(catalogue: Catalogue) -> dict[str, int]:
  platforms = catalogue.platforms
  assets = catalogue.assets
  return {
    'assets': len(assets),
    'platforms': len(platforms),
    'blockchains': sum(1 for platform in platforms.values() if platform['kind'] == 'blockchain'),
    'cexs': sum(1 for platform in platforms.values() if platform['kind'] == 'cex'),
    'dexs': sum(1 for platform in platforms.values() if platform['kind'] == 'dex'),
    'asset_translations': len(catalogue.asset_translations),
    'network_translations': len(catalogue.network_translations),
    'assets_with_icons': sum(1 for asset in assets.values() if 'icon' in asset),
    'assets_with_external_ids': sum(1 for asset in assets.values() if asset.get('external')),
    'assets_with_pegs': sum(1 for asset in assets.values() if 'pegged_to' in asset),
    'spam_platforms': len(catalogue.spam),
  }


def build_root_html() -> str:
  return '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tribulnation Catalogue</title>
  <meta http-equiv="refresh" content="0; url=api/">
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; max-width: 60rem; line-height: 1.5; }
  </style>
</head>
<body>
  <h1>Tribulnation Catalogue</h1>
  <p><a href="api/">Open the API index</a>.</p>
</body>
</html>
'''


def build_api_html(stats_data: dict[str, int]) -> str:
  return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tribulnation Catalogue API</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; max-width: 60rem; line-height: 1.5; }}
    code {{ background: #f4f4f4; padding: 0.1rem 0.25rem; border-radius: 0.25rem; }}
    li {{ margin: 0.25rem 0; }}
  </style>
</head>
<body>
  <h1>Tribulnation Catalogue API</h1>
  <p>Static JSON API for crypto assets, platforms, translations, instruments, and spam addresses.</p>
  <ul>
    <li><a href="stats.json">Stats</a>: {stats_data['assets']} assets, {stats_data['platforms']} platforms</li>
    <li><a href="assets.json">Assets</a></li>
    <li><a href="platforms.json">Platforms</a></li>
    <li><a href="platforms/blockchains.json">Blockchains</a></li>
    <li><a href="indexes/symbols.json">Symbol index</a></li>
    <li><a href="indexes/pegs.json">Peg index</a></li>
    <li><a href="indexes/external/coingecko.json">CoinGecko index</a></li>
  </ul>
  <p>See <code>APIv2.md</code> in the repository for the route specification.</p>
</body>
</html>
'''


def build_directory_html(title: str, entries: list[tuple[str, str]]) -> str:
  links = '\n'.join(
    f'    <li><a href="{escape(href)}"><code>{escape(name)}</code></a></li>'
    for name, href in entries
  )
  return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; max-width: 60rem; line-height: 1.5; }}
    code {{ background: #f4f4f4; padding: 0.1rem 0.25rem; border-radius: 0.25rem; }}
    li {{ margin: 0.25rem 0; }}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  <ul>
{links}
  </ul>
</body>
</html>
'''


def write_directory_indexes(root: Path):
  for directory in sorted(path for path in root.rglob('*') if path.is_dir()):
    if directory == root:
      continue
    entries: list[tuple[str, str]] = []
    parent = directory.parent
    if parent != root.parent:
      entries.append(('..', '../'))
    for child in sorted(directory.iterdir(), key=lambda item: (not item.is_dir(), item.name)):
      if child.name == 'index.html':
        continue
      name = child.name + ('/' if child.is_dir() else '')
      href = quote(child.name) + ('/' if child.is_dir() else '')
      entries.append((name, href))
    title = '/' + directory.relative_to(root.parent).as_posix()
    (directory / 'index.html').write_text(build_directory_html(title, entries))


def copy_icons(root: Path, output: Path):
  src = root / 'icons'
  dst = output / 'icons'
  if not src.exists():
    return
  if dst.exists():
    shutil.rmtree(dst)
  shutil.copytree(src, dst)


def copy_ui(root: Path, output: Path):
  ui = root / 'ui'
  if not ui.exists():
    (output / 'index.html').write_text(build_root_html())
    return

  index = ui / 'index.html'
  if index.exists():
    shutil.copy2(index, output / 'index.html')
  else:
    (output / 'index.html').write_text(build_root_html())

  for item in sorted(ui.iterdir()):
    if item.name in {'index.html', 'api', 'icons'}:
      continue
    destination = output / item.name
    if destination.exists():
      if destination.is_dir():
        shutil.rmtree(destination)
      else:
        destination.unlink()
    if item.is_dir():
      shutil.copytree(item, destination)
    else:
      shutil.copy2(item, destination)


def default_output(root: Path) -> Path:
  if (root / 'app').exists():
    return root / 'app' / 'static'
  if (root / 'ui').exists():
    return root / 'ui' / 'static'
  return root / 'public'


def should_write_site_html(root: Path, output: Path) -> bool:
  for app_root in (root / 'app', root / 'ui'):
    try:
      output.relative_to(app_root)
      return False
    except ValueError:
      pass
  return True


def should_write_api_html(root: Path, output: Path) -> bool:
  return should_write_site_html(root, output)


def build(args: argparse.Namespace):
  root = Path.cwd()
  data = Path(args.data)
  output = Path(args.output) if args.output else default_output(root)
  api = output / 'api'
  public_url = clean_public_url(args.public_url)

  catalogue = load.all(data)
  errors = validate.all(catalogue, str(root))
  if errors:
    for error in errors:
      print(error, file=sys.stderr)
    raise SystemExit(1)

  if api.exists():
    shutil.rmtree(api)
  api.mkdir(parents=True, exist_ok=True)
  output.mkdir(parents=True, exist_ok=True)

  stats_data = stats(catalogue)
  write_json(api / 'stats.json', stats_data)

  assets = [
    asset_summary(id, asset, public_url)
    for id, asset in sorted(catalogue.assets.items())
  ]
  write_json(api / 'assets.json', assets)
  for id, asset in sorted(catalogue.assets.items()):
    write_json(api / 'assets' / f'{id}.json', with_id(id, asset, public_url))
    for locale, about in sorted(asset.get('about', {}).items()):
      write_json(api / 'assets' / id / f'{locale}.json', localized_asset(id, asset, public_url, locale, about))

  platforms = [
    platform_summary(id, platform, public_url)
    for id, platform in sorted(catalogue.platforms.items())
  ]
  write_json(api / 'platforms.json', platforms)
  for id, platform in sorted(catalogue.platforms.items()):
    write_json(api / 'platforms' / f'{id}.json', with_id(id, platform, public_url))

  blockchains = [
    platform_summary(id, platform, public_url, blockchain=True)
    for id, platform in sorted(catalogue.platforms.items())
    if platform['kind'] == 'blockchain'
  ]
  cexs = [
    platform_summary(id, platform, public_url)
    for id, platform in sorted(catalogue.platforms.items())
    if platform['kind'] == 'cex'
  ]
  dexs = [
    platform_summary(id, platform, public_url)
    for id, platform in sorted(catalogue.platforms.items())
    if platform['kind'] == 'dex'
  ]
  write_json(api / 'platforms' / 'blockchains.json', blockchains)
  write_json(api / 'platforms' / 'cexs.json', cexs)
  write_json(api / 'platforms' / 'dexs.json', dexs)

  for platform, translations in sorted(catalogue.asset_translations.items()):
    write_json(api / 'translations' / 'assets' / f'{platform}.json', dict(sorted(translations.items())))
  for platform, translations in sorted(catalogue.network_translations.items()):
    write_json(api / 'translations' / 'networks' / f'{platform}.json', dict(sorted(translations.items())))

  write_json(api / 'instruments' / 'spot.json', platform_index(catalogue.spot_instruments))
  write_json(api / 'instruments' / 'perpetual.json', platform_index(catalogue.perpetual_instruments))
  write_json(api / 'instruments' / 'debt.json', platform_index(catalogue.debt_instruments))
  write_json(api / 'instruments' / 'collateral.json', platform_index(catalogue.collateral_instruments))
  write_json(api / 'instruments' / 'pools.json', platform_index(catalogue.pools))
  write_platform_maps(api / 'instruments' / 'spot', catalogue.spot_instruments)
  write_platform_maps(api / 'instruments' / 'perpetual', catalogue.perpetual_instruments)
  write_platform_maps(api / 'instruments' / 'debt', catalogue.debt_instruments)
  write_platform_maps(api / 'instruments' / 'collateral', catalogue.collateral_instruments)
  write_platform_maps(api / 'instruments' / 'pools', catalogue.pools)

  for asset, refs in instrument_index(catalogue).items():
    write_json(api / 'instruments' / 'index' / f'{asset}.json', refs)

  for platform, addresses in sorted(catalogue.spam.items()):
    write_json(api / 'spam' / f'{platform}.json', keyed_records(addresses))

  write_json(api / 'indexes' / 'symbols.json', symbols_index(catalogue))
  write_json(api / 'indexes' / 'external' / 'coingecko.json', external_index(catalogue, 'coingecko'))
  write_json(api / 'indexes' / 'pegs.json', pegs_index(catalogue))

  copy_icons(root, output)
  if should_write_site_html(root, output):
    copy_ui(root, output)
  if should_write_api_html(root, output):
    write_directory_indexes(api)
    (api / 'index.html').write_text(build_api_html(stats_data))


def main():
  build(parse_args())


if __name__ == '__main__':
  main()
