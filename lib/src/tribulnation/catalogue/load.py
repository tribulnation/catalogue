from collections import defaultdict
from pathlib import Path
from pydantic import TypeAdapter
from .schema import Asset, Platform, Catalogue, Spot, Perpetual, Debt, Collateral, SpamToken, Pool

_asset_adapter = TypeAdapter(Asset)
_platform_adapter = TypeAdapter(Platform)
_asset_translation_adapter = TypeAdapter(dict[str, str])
_network_translation_adapter = TypeAdapter(dict[str, str])
_spot_instruments_adapter = TypeAdapter(dict[str, Spot])
_perpetual_instruments_adapter = TypeAdapter(dict[str, Perpetual])
_debt_instruments_adapter = TypeAdapter(dict[str, Debt])
_collateral_instruments_adapter = TypeAdapter(dict[str, Collateral])
_spam_tokens_adapter = TypeAdapter(dict[str, SpamToken])
_pools_adapter = TypeAdapter(dict[str, Pool])

def assets(folder: Path) -> dict[str, Asset]:
  assets: dict[str, Asset] = {}
  for file in folder.glob('*.json'):
    id = file.stem
    assets[id] = _asset_adapter.validate_json(file.read_bytes(), extra='forbid')
  return assets

def assets_order(file: Path) -> list[str]:
  return [id for line in file.read_text().splitlines() if (id := line.strip())]

def platforms(folder: Path) -> dict[str, Platform]:
  platforms: dict[str, Platform] = {}
  for file in folder.glob('*.json'):
    id = file.stem
    platforms[id] = _platform_adapter.validate_json(file.read_bytes(), extra='forbid')
  return platforms

def platforms_order(file: Path) -> list[str]:
  return [id for line in file.read_text().splitlines() if (id := line.strip())]

def network_translations(folder: Path) -> dict[str, dict[str, str]]:
  network_translations = defaultdict[str, dict[str, str]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    network_translations[platform].update(_network_translation_adapter.validate_json(file.read_bytes()))

  return dict(network_translations)

def asset_translations(folder: Path) -> dict[str, dict[str, str]]:
  asset_translations = defaultdict[str, dict[str, str]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    asset_translations[platform].update(_asset_translation_adapter.validate_json(file.read_bytes()))
  return dict(asset_translations) 

def spot_instruments(folder: Path) -> dict[str, dict[str, Spot]]:
  spot_instruments = defaultdict[str, dict[str, Spot]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    spot_instruments[platform].update(_spot_instruments_adapter.validate_json(file.read_bytes()))
  return dict(spot_instruments)

def perpetual_instruments(folder: Path) -> dict[str, dict[str, Perpetual]]:
  perpetual_instruments = defaultdict[str, dict[str, Perpetual]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    perpetual_instruments[platform].update(_perpetual_instruments_adapter.validate_json(file.read_bytes()))
  return dict(perpetual_instruments)

def debt_instruments(folder: Path) -> dict[str, dict[str, Debt]]:
  debt_instruments = defaultdict[str, dict[str, Debt]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    debt_instruments[platform].update(_debt_instruments_adapter.validate_json(file.read_bytes()))
  return dict(debt_instruments)

def collateral_instruments(folder: Path) -> dict[str, dict[str, Collateral]]:
  collateral_instruments = defaultdict[str, dict[str, Collateral]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    collateral_instruments[platform].update(_collateral_instruments_adapter.validate_json(file.read_bytes()))
  return dict(collateral_instruments)

def spam_tokens(folder: Path) -> dict[str, dict[str, SpamToken]]:
  spam_tokens = defaultdict[str, dict[str, SpamToken]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    spam_tokens[platform].update(_spam_tokens_adapter.validate_json(file.read_bytes()))
  return dict(spam_tokens)

def pools(folder: Path) -> dict[str, dict[str, Pool]]:
  pools = defaultdict[str, dict[str, Pool]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    pools[platform].update(_pools_adapter.validate_json(file.read_bytes()))
  return dict(pools)

def all(folder: Path | str) -> Catalogue:
  folder = Path(folder)
  return Catalogue(
    assets=assets(folder / 'assets'),
    platforms=platforms(folder / 'platforms'),
    platforms_order=platforms_order(folder / 'platforms' / 'order.txt'),
    network_translations=network_translations(folder / 'network_translations'),
    asset_translations=asset_translations(folder / 'asset_translations'),
    spot_instruments=spot_instruments(folder / 'instruments' / 'spot'),
    perpetual_instruments=perpetual_instruments(folder / 'instruments' / 'perpetual'),
    debt_instruments=debt_instruments(folder / 'instruments' / 'debt'),
    collateral_instruments=collateral_instruments(folder / 'instruments' / 'collateral'),
    pools=pools(folder / 'pools'),
    spam_tokens=spam_tokens(folder / 'spam_tokens'),
  )
