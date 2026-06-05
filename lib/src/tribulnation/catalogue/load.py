import os as _os
from collections import defaultdict as _defaultdict
from glob import glob as _glob
from pydantic import TypeAdapter as _TypeAdapter
from .schema import Asset, Platform, Catalogue, Spot, Perpetual, Debt, Collateral, SpamToken

_asset_adapter = _TypeAdapter(Asset)
_platform_adapter = _TypeAdapter(Platform)
_asset_translation_adapter = _TypeAdapter(dict[str, str])
_network_translation_adapter = _TypeAdapter(dict[str, str])
_spot_instruments_adapter = _TypeAdapter(dict[str, Spot])
_perpetual_instruments_adapter = _TypeAdapter(dict[str, Perpetual])
_debt_instruments_adapter = _TypeAdapter(dict[str, Debt])
_collateral_instruments_adapter = _TypeAdapter(dict[str, Collateral])
_spam_tokens_adapter = _TypeAdapter(dict[str, SpamToken])

def assets(folder: str) -> dict[str, Asset]:
  assets: dict[str, Asset] = {}
  for file in _glob(_os.path.join(folder, '*.json')):
    id = file.split('/')[-1].split('.')[0]
    with open(file) as f:
      assets[id] = _asset_adapter.validate_json(f.read(), extra='forbid')
  return assets

def assets_order(file: str) -> list[str]:
  with open(file) as f:
    return [line.strip() for line in f if line.strip()]

def platforms(folder: str) -> dict[str, Platform]:
  platforms: dict[str, Platform] = {}
  for file in _glob(_os.path.join(folder, '*.json')):
    id = file.split('/')[-1].split('.')[0]
    with open(file) as f:
      platforms[id] = _platform_adapter.validate_json(f.read(), extra='forbid')
  return platforms

def platforms_order(file: str) -> list[str]:
  with open(file) as f:
    return [line.strip() for line in f if line.strip()]

def network_translations(folder: str) -> dict[str, dict[str, str]]:
  network_translations = _defaultdict[str, dict[str, str]](dict)
  for file in _glob(_os.path.join(folder, '*.json')):
    platform = file.split('/')[-1].split('.')[0]
    with open(file) as f:
      network_translations[platform].update(_network_translation_adapter.validate_json(f.read()))

  return network_translations

def asset_translations(folder: str) -> dict[str, dict[str, str]]:
  asset_translations = _defaultdict[str, dict[str, str]](dict)
  for file in _glob(_os.path.join(folder, '*.json')):
    platform = file.split('/')[-1].split('.')[0]
    with open(file) as f:
      asset_translations[platform].update(_asset_translation_adapter.validate_json(f.read()))
  return asset_translations

def spot_instruments(folder: str) -> dict[str, dict[str, Spot]]:
  spot_instruments = _defaultdict[str, dict[str, Spot]](dict)
  for file in _glob(_os.path.join(folder, '*.json')):
    platform = file.split('/')[-1].split('.')[0]
    with open(file) as f:
      spot_instruments[platform].update(_spot_instruments_adapter.validate_json(f.read()))
  return spot_instruments

def perpetual_instruments(folder: str) -> dict[str, dict[str, Perpetual]]:
  perpetual_instruments = _defaultdict[str, dict[str, Perpetual]](dict)
  for file in _glob(_os.path.join(folder, '*.json')):
    platform = file.split('/')[-1].split('.')[0]
    with open(file) as f:
      perpetual_instruments[platform].update(_perpetual_instruments_adapter.validate_json(f.read()))
  return perpetual_instruments

def debt_instruments(folder: str) -> dict[str, dict[str, Debt]]:
  debt_instruments = _defaultdict[str, dict[str, Debt]](dict)
  for file in _glob(_os.path.join(folder, '*.json')):
    platform = file.split('/')[-1].split('.')[0]
    with open(file) as f:
      debt_instruments[platform].update(_debt_instruments_adapter.validate_json(f.read()))
  return debt_instruments

def collateral_instruments(folder: str) -> dict[str, dict[str, Collateral]]:
  collateral_instruments = _defaultdict[str, dict[str, Collateral]](dict)
  for file in _glob(_os.path.join(folder, '*.json')):
    platform = file.split('/')[-1].split('.')[0]
    with open(file) as f:
      collateral_instruments[platform].update(_collateral_instruments_adapter.validate_json(f.read()))
  return collateral_instruments

def spam_tokens(folder: str) -> dict[str, dict[str, SpamToken]]:
  spam_tokens = _defaultdict[str, dict[str, SpamToken]](dict)
  for file in _glob(_os.path.join(folder, '*.json')):
    platform = file.split('/')[-1].split('.')[0]
    with open(file) as f:
      spam_tokens[platform].update(_spam_tokens_adapter.validate_json(f.read()))
  return spam_tokens

def all(folder: str) -> Catalogue:
  return Catalogue(
    assets=assets(_os.path.join(folder, 'assets')),
    assets_order=assets_order(_os.path.join(folder, 'assets', 'order.txt')),
    platforms=platforms(_os.path.join(folder, 'platforms')),
    platforms_order=platforms_order(_os.path.join(folder, 'platforms', 'order.txt')),
    network_translations=network_translations(_os.path.join(folder, 'network_translations')),
    asset_translations=asset_translations(_os.path.join(folder, 'asset_translations')),
    spot_instruments=spot_instruments(_os.path.join(folder, 'instruments', 'spot')),
    perpetual_instruments=perpetual_instruments(_os.path.join(folder, 'instruments', 'perpetual')),
    debt_instruments=debt_instruments(_os.path.join(folder, 'instruments', 'debt')),
    collateral_instruments=collateral_instruments(_os.path.join(folder, 'instruments', 'collateral')),
    spam_tokens=spam_tokens(_os.path.join(folder, 'spam_tokens')),
  )
