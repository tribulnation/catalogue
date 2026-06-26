#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from html import escape
from pathlib import Path
from urllib.parse import quote, urljoin

from pydantic import BaseModel

from tribulnation.catalogue.data import load, validate
from tribulnation.catalogue.data.main import Catalogue
from tribulnation.catalogue.api.schema import (
  Stats,
  AssetPeg, ExternalIds, AssetSummary, AssetDetail, LocalizedAssetDetail,
  PlatformSummary, PlatformDetail, BlockchainSummary, CexSummary, DexSummary,
  InstrumentPlatformEntry,
  SpotInstrument, PerpetualInstrument, DebtInstrument, CollateralInstrument, PoolInstrument,
  InstrumentReference,
  SpamAddress,
)


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description='Build the static catalogue API.')
  parser.add_argument('--data', default='data', help='Catalogue data directory.')
  parser.add_argument(
    '--output',
    help='Static asset output directory. Defaults to app/static when app/ exists, otherwise public.',
  )
  parser.add_argument('--public-url', help='Optional public base URL for generated absolute asset URLs.')
  return parser.parse_args()


def _serializable(data: object) -> object:
  if isinstance(data, BaseModel):
    return data.model_dump(exclude_none=True)
  if isinstance(data, list):
    return [_serializable(item) for item in data]
  if isinstance(data, dict):
    return {k: _serializable(v) for k, v in data.items()}
  return data


def write_json(path: Path, data: object) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(
    json.dumps(_serializable(data), ensure_ascii=False, indent=2, sort_keys=True) + '\n'
  )


def clean_public_url(public_url: str | None) -> str | None:
  if public_url is None:
    return None
  return public_url.rstrip('/') + '/'


def public_path(public_url: str | None, path: str) -> str:
  if public_url is None:
    return '/' + path.lstrip('/')
  return urljoin(public_url, path.lstrip('/'))


def asset_summary(id: str, asset: dict, public_url: str | None) -> AssetSummary:
  icon = asset.get('icon')
  peg = asset.get('pegged_to')
  return AssetSummary(
    id=id,
    display_name=asset['display_name'],
    symbol=asset['symbol'],
    icon=public_path(public_url, icon) if icon else None,
    tags=asset.get('tags'),
    pegged_to=AssetPeg(**peg) if peg else None,
  )


def asset_detail(id: str, asset: dict, public_url: str | None) -> AssetDetail:
  icon = asset.get('icon')
  peg = asset.get('pegged_to')
  ext = asset.get('external')
  return AssetDetail(
    id=id,
    display_name=asset['display_name'],
    symbol=asset['symbol'],
    icon=public_path(public_url, icon) if icon else None,
    tags=asset.get('tags'),
    urls=asset.get('urls'),
    about=asset.get('about'),
    external=ExternalIds(**ext) if ext else None,
    pegged_to=AssetPeg(**peg) if peg else None,
  )


def localized_asset(id: str, asset: dict, public_url: str | None, locale: str, about: str) -> LocalizedAssetDetail:
  icon = asset.get('icon')
  peg = asset.get('pegged_to')
  ext = asset.get('external')
  return LocalizedAssetDetail(
    id=id,
    display_name=asset['display_name'],
    symbol=asset['symbol'],
    icon=public_path(public_url, icon) if icon else None,
    tags=asset.get('tags'),
    urls=asset.get('urls'),
    about=about,
    external=ExternalIds(**ext) if ext else None,
    pegged_to=AssetPeg(**peg) if peg else None,
  )


def platform_summary(id: str, platform: dict, public_url: str | None) -> PlatformSummary:
  icon = platform.get('icon')
  return PlatformSummary(
    id=id,
    display_name=platform['display_name'],
    kind=platform['kind'],
    icon=public_path(public_url, icon) if icon else None,
  )


def blockchain_summary(id: str, platform: dict, public_url: str | None) -> BlockchainSummary:
  icon = platform.get('icon')
  return BlockchainSummary(
    id=id,
    display_name=platform['display_name'],
    kind='blockchain',
    icon=public_path(public_url, icon) if icon else None,
    native_asset=platform.get('native_asset'),
    category=platform.get('category'),
    namespace=platform.get('namespace'),
    chain_id=platform.get('chain_id'),
  )


def cex_summary(id: str, platform: dict, public_url: str | None) -> CexSummary:
  icon = platform.get('icon')
  return CexSummary(
    id=id,
    display_name=platform['display_name'],
    kind='cex',
    icon=public_path(public_url, icon) if icon else None,
  )


def dex_summary(id: str, platform: dict, public_url: str | None) -> DexSummary:
  icon = platform.get('icon')
  return DexSummary(
    id=id,
    display_name=platform['display_name'],
    kind='dex',
    icon=public_path(public_url, icon) if icon else None,
  )


def platform_detail(id: str, platform: dict, public_url: str | None) -> PlatformDetail:
  icon = platform.get('icon')
  return PlatformDetail(
    id=id,
    display_name=platform['display_name'],
    kind=platform['kind'],
    icon=public_path(public_url, icon) if icon else None,
    urls=platform.get('urls'),
    about=platform.get('about'),
    native_asset=platform.get('native_asset'),
    category=platform.get('category'),
    namespace=platform.get('namespace'),
    chain_id=platform.get('chain_id'),
  )


def platform_index(maps: dict) -> list[InstrumentPlatformEntry]:
  return [
    InstrumentPlatformEntry(platform=platform, count=len(items))
    for platform, items in sorted(maps.items())
  ]


def spot_instruments(items: dict) -> dict[str, SpotInstrument]:
  return {id: SpotInstrument(id=id, **item) for id, item in sorted(items.items())}


def perpetual_instruments(items: dict) -> dict[str, PerpetualInstrument]:
  return {id: PerpetualInstrument(id=id, **item) for id, item in sorted(items.items())}


def debt_instruments(items: dict) -> dict[str, DebtInstrument]:
  return {id: DebtInstrument(id=id, **item) for id, item in sorted(items.items())}


def collateral_instruments(items: dict) -> dict[str, CollateralInstrument]:
  return {id: CollateralInstrument(id=id, **item) for id, item in sorted(items.items())}


def pool_instruments(items: dict) -> dict[str, PoolInstrument]:
  return {id: PoolInstrument(id=id, **item) for id, item in sorted(items.items())}


def instrument_index(catalogue: Catalogue) -> dict[str, list[InstrumentReference]]:
  index: dict[str, list[InstrumentReference]] = {}

  def add(asset: str, ref: InstrumentReference) -> None:
    index.setdefault(asset, []).append(ref)

  for platform, instruments in catalogue.spot_instruments.items():
    for id, inst in instruments.items():
      add(inst['base'], InstrumentReference(kind='spot', platform=platform, id=id, role='base'))
      add(inst['quote'], InstrumentReference(kind='spot', platform=platform, id=id, role='quote'))

  for platform, instruments in catalogue.perpetual_instruments.items():
    for id, inst in instruments.items():
      add(inst['base'], InstrumentReference(kind='perpetual', platform=platform, id=id, role='base'))
      add(inst['quote'], InstrumentReference(kind='perpetual', platform=platform, id=id, role='quote'))
      add(inst['settlement'], InstrumentReference(kind='perpetual', platform=platform, id=id, role='settlement'))

  for platform, instruments in catalogue.debt_instruments.items():
    for id, inst in instruments.items():
      add(inst['asset'], InstrumentReference(kind='debt', platform=platform, id=id, role='asset'))

  for platform, instruments in catalogue.collateral_instruments.items():
    for id, inst in instruments.items():
      add(inst['asset'], InstrumentReference(kind='collateral', platform=platform, id=id, role='asset'))

  for platform, pools in catalogue.pools.items():
    for id, pool in pools.items():
      for asset in pool['assets']:
        add(asset, InstrumentReference(kind='pool', platform=platform, id=id, role='asset'))

  return {
    asset: sorted(refs, key=lambda r: (r.kind, r.platform, r.id, r.role))
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


def stats(catalogue: Catalogue) -> Stats:
  platforms = catalogue.platforms
  assets = catalogue.assets
  return Stats(
    assets=len(assets),
    platforms=len(platforms),
    blockchains=sum(1 for p in platforms.values() if p['kind'] == 'blockchain'),
    cexs=sum(1 for p in platforms.values() if p['kind'] == 'cex'),
    dexs=sum(1 for p in platforms.values() if p['kind'] == 'dex'),
    asset_translations=sum(len(t) for t in catalogue.asset_translations.values()),
    network_translations=sum(len(t) for t in catalogue.network_translations.values()),
    spot_instruments=sum(len(i) for i in catalogue.spot_instruments.values()),
    perpetual_instruments=sum(len(i) for i in catalogue.perpetual_instruments.values()),
    assets_with_icons=sum(1 for a in assets.values() if 'icon' in a),
    assets_with_external_ids=sum(1 for a in assets.values() if a.get('external')),
    assets_with_pegs=sum(1 for a in assets.values() if 'pegged_to' in a),
    spam_addresses=sum(len(a) for a in catalogue.spam.values()),
  )


def write_stats_svg(s: Stats, path: Path) -> None:
  instruments = s.spot_instruments + s.perpetual_instruments
  translations = s.asset_translations + s.network_translations
  cols = [
    (str(s.assets), 'assets'),
    (str(s.platforms), 'platforms'),
    (str(instruments), 'instruments'),
    (str(translations), 'translations'),
    (str(s.assets_with_icons), 'icons'),
  ]
  n = len(cols)
  w, h, col_w = 600, 56, 600 // n
  cells = ''.join(
    f'<text class="n" x="{col_w * i + col_w // 2}" y="26" text-anchor="middle">{num}</text>'
    f'<text class="l" x="{col_w * i + col_w // 2}" y="42" text-anchor="middle">{label}</text>'
    for i, (num, label) in enumerate(cols)
  )
  seps = ''.join(
    f'<line class="s" x1="{col_w * i}" y1="10" x2="{col_w * i}" y2="46"/>'
    for i in range(1, n)
  )
  svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"'
    f' viewBox="0 0 {w} {h}" role="img" aria-label="Catalogue stats">\n'
    '<style>\n'
    '.bg{fill:#f6f8fa}.n{font:bold 18px system-ui,sans-serif;fill:#1f2328}'
    '.l{font:11px system-ui,sans-serif;fill:#57606a}.s{stroke:#d0d7de;stroke-width:1}\n'
    '@media(prefers-color-scheme:dark){'
    '.bg{fill:#161b22}.n{fill:#e6edf3}.l{fill:#8b949e}.s{stroke:#30363d}}\n'
    '</style>\n'
    f'<rect class="bg" width="{w}" height="{h}" rx="6"/>\n'
    f'{seps}{cells}\n</svg>\n'
  )
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(svg)


def write_zip(src: Path, dst: Path) -> None:
  if not src.exists():
    return
  dst.parent.mkdir(parents=True, exist_ok=True)
  with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zf:
    for file in sorted(src.rglob('*')):
      if file.is_file():
        zf.write(file, file.relative_to(src))


def write_openapi(api: Path, public_url: str | None = None) -> None:
  from tribulnation.catalogue.api.api import app
  spec = app.openapi()
  if public_url:
    spec['servers'] = [{'url': public_url}]
  write_json(api / 'openapi.json', spec)


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


def build_api_html(stats_data: Stats) -> str:
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
    <li><a href="stats.json">Stats</a>: {stats_data.assets} assets, {stats_data.platforms} platforms</li>
    <li><a href="assets.json">Assets</a></li>
    <li><a href="platforms.json">Platforms</a></li>
    <li><a href="platforms/blockchains.json">Blockchains</a></li>
    <li><a href="indexes/symbols.json">Symbol index</a></li>
    <li><a href="indexes/pegs.json">Peg index</a></li>
    <li><a href="indexes/external/coingecko.json">CoinGecko index</a></li>
    <li><a href="openapi.json">OpenAPI spec</a></li>
  </ul>
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


def write_directory_indexes(root: Path) -> None:
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


def copy_icons(root: Path, output: Path) -> None:
  src = root / 'icons'
  dst = output / 'icons'
  if not src.exists():
    return
  if dst.exists():
    shutil.rmtree(dst)
  shutil.copytree(src, dst)


def copy_ui(root: Path, output: Path) -> None:
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


def build(args: argparse.Namespace) -> None:
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
  write_stats_svg(stats_data, output / 'stats.svg')

  write_json(api / 'assets.json', [
    asset_summary(id, asset, public_url)
    for id, asset in sorted(catalogue.assets.items())
  ])
  for id, asset in sorted(catalogue.assets.items()):
    write_json(api / 'assets' / f'{id}.json', asset_detail(id, asset, public_url))
    for locale, about in sorted(asset.get('about', {}).items()):
      write_json(api / 'assets' / id / f'{locale}.json', localized_asset(id, asset, public_url, locale, about))

  write_json(api / 'platforms.json', [
    platform_summary(id, platform, public_url)
    for id, platform in sorted(catalogue.platforms.items())
  ])
  for id, platform in sorted(catalogue.platforms.items()):
    write_json(api / 'platforms' / f'{id}.json', platform_detail(id, platform, public_url))

  write_json(api / 'platforms' / 'blockchains.json', [
    blockchain_summary(id, p, public_url)
    for id, p in sorted(catalogue.platforms.items()) if p['kind'] == 'blockchain'
  ])
  write_json(api / 'platforms' / 'cexs.json', [
    cex_summary(id, p, public_url)
    for id, p in sorted(catalogue.platforms.items()) if p['kind'] == 'cex'
  ])
  write_json(api / 'platforms' / 'dexs.json', [
    dex_summary(id, p, public_url)
    for id, p in sorted(catalogue.platforms.items()) if p['kind'] == 'dex'
  ])

  for platform, translations in sorted(catalogue.asset_translations.items()):
    write_json(api / 'translations' / 'assets' / f'{platform}.json', dict(sorted(translations.items())))
  for platform, translations in sorted(catalogue.network_translations.items()):
    write_json(api / 'translations' / 'networks' / f'{platform}.json', dict(sorted(translations.items())))

  write_json(api / 'instruments' / 'spot.json', platform_index(catalogue.spot_instruments))
  write_json(api / 'instruments' / 'perpetual.json', platform_index(catalogue.perpetual_instruments))
  write_json(api / 'instruments' / 'debt.json', platform_index(catalogue.debt_instruments))
  write_json(api / 'instruments' / 'collateral.json', platform_index(catalogue.collateral_instruments))
  write_json(api / 'instruments' / 'pools.json', platform_index(catalogue.pools))

  for platform, items in sorted(catalogue.spot_instruments.items()):
    write_json(api / 'instruments' / 'spot' / f'{platform}.json', spot_instruments(items))
  for platform, items in sorted(catalogue.perpetual_instruments.items()):
    write_json(api / 'instruments' / 'perpetual' / f'{platform}.json', perpetual_instruments(items))
  for platform, items in sorted(catalogue.debt_instruments.items()):
    write_json(api / 'instruments' / 'debt' / f'{platform}.json', debt_instruments(items))
  for platform, items in sorted(catalogue.collateral_instruments.items()):
    write_json(api / 'instruments' / 'collateral' / f'{platform}.json', collateral_instruments(items))
  for platform, items in sorted(catalogue.pools.items()):
    write_json(api / 'instruments' / 'pools' / f'{platform}.json', pool_instruments(items))

  for asset, refs in instrument_index(catalogue).items():
    write_json(api / 'instruments' / 'index' / f'{asset}.json', refs)

  for platform, addresses in sorted(catalogue.spam.items()):
    write_json(api / 'spam' / f'{platform}.json', {
      addr: SpamAddress(**record) for addr, record in sorted(addresses.items())
    })

  write_json(api / 'indexes' / 'symbols.json', symbols_index(catalogue))
  write_json(api / 'indexes' / 'external' / 'coingecko.json', external_index(catalogue, 'coingecko'))
  write_json(api / 'indexes' / 'pegs.json', pegs_index(catalogue))

  write_openapi(api, public_url)

  write_zip(root / 'data', output / 'data.zip')
  write_zip(root / 'icons', output / 'icons.zip')

  copy_icons(root, output)
  if should_write_site_html(root, output):
    copy_ui(root, output)
  if should_write_api_html(root, output):
    write_directory_indexes(api)
    (api / 'index.html').write_text(build_api_html(stats_data))


def main() -> None:
  build(parse_args())


if __name__ == '__main__':
  main()
