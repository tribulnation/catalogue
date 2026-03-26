import os as _os
from collections import defaultdict as _defaultdict
from glob import glob as _glob
from pydantic import TypeAdapter as _TypeAdapter
from .schema import Asset, Platform, Network, Catalogue, Spot, Perpetual, Debt

_asset_adapter = _TypeAdapter(Asset)
_platform_adapter = _TypeAdapter(Platform)
_network_adapter = _TypeAdapter(Network)
_asset_translation_adapter = _TypeAdapter(dict[str, str])
_network_translation_adapter = _TypeAdapter(dict[str, str])
_spot_instruments_adapter = _TypeAdapter(dict[str, Spot])
_perpetual_instruments_adapter = _TypeAdapter(dict[str, Perpetual])
_debt_instruments_adapter = _TypeAdapter(dict[str, Debt])

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

def networks(folder: str) -> dict[str, Network]:
  networks: dict[str, Network] = {}
  for file in _glob(_os.path.join(folder, '*.json')):
    id = file.split('/')[-1].split('.')[0]
    with open(file) as f:
      networks[id] = _network_adapter.validate_json(f.read(), extra='forbid')
  return networks

def networks_order(file: str) -> list[str]:
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

def all(folder: str) -> Catalogue:
  return Catalogue(
    assets=assets(_os.path.join(folder, 'assets')),
    assets_order=assets_order(_os.path.join(folder, 'assets', 'order.txt')),
    platforms=platforms(_os.path.join(folder, 'platforms')),
    platforms_order=platforms_order(_os.path.join(folder, 'platforms', 'order.txt')),
    networks=networks(_os.path.join(folder, 'networks')),
    networks_order=networks_order(_os.path.join(folder, 'networks', 'order.txt')),
    network_translations=network_translations(_os.path.join(folder, 'network_translations')),
    asset_translations=asset_translations(_os.path.join(folder, 'asset_translations')),
    spot_instruments=spot_instruments(_os.path.join(folder, 'instruments', 'spot')),
    perpetual_instruments=perpetual_instruments(_os.path.join(folder, 'instruments', 'perpetual')),
    debt_instruments=debt_instruments(_os.path.join(folder, 'instruments', 'debt')),
  )