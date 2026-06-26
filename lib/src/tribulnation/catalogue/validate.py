import os as _os
import re as _re
from typing import Mapping
from .schema import Asset, Platform, Catalogue, Spot, Perpetual, Debt, Collateral, Pool

_id_pattern = _re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

def ids(kind: str, items: Mapping[str, object]):
  errors: list[str] = []
  for id in items:
    if not _id_pattern.fullmatch(id):
      errors.append(f'[{kind} ID ERROR] Invalid id "{id}". IDs must be lowercase kebab-case')
  return errors

def platform_keys(kind: str, platforms: Mapping[str, Platform], items: Mapping[str, object]):
  errors: list[str] = []
  for platform in items:
    if platform not in platforms:
      errors.append(f'[{kind} PLATFORM ERROR] Unknown platform id "{platform}"')
  return errors

def asset_icons(assets: Mapping[str, Asset], base_folder: str):
  errors: list[str] = []
  for id, asset in assets.items():
    if (icon := asset.get('icon')) is not None:
      if not _os.path.exists(_os.path.join(base_folder, icon)):
        errors.append(f'[ASSET ICON ERROR] Asset "{id}" has inexistent icon "{icon}"')
  return errors

def platform_icons(platforms: Mapping[str, Platform], base_folder: str):
  errors: list[str] = []
  for id, platform in platforms.items():
    if (icon := platform.get('icon')) is not None:
      if not _os.path.exists(_os.path.join(base_folder, icon)):
        errors.append(f'[PLATFORM ICON ERROR] Platform "{id}" has inexistent icon "{icon}"')
  return errors

def native_assets(assets: Mapping[str, Asset], platforms: Mapping[str, Platform]):
  errors: list[str] = []
  for id, platform in platforms.items():
    if platform['kind'] == 'blockchain':
      if (asset := platform.get('native_asset')) is not None:  # type: ignore[union-attr]
        if asset not in assets:
          errors.append(f'[NATIVE ASSET ERROR] Blockchain "{id}" has inexistent native asset "{asset}"')
  return errors

def asset_pegs(assets: Mapping[str, Asset]):
  errors: list[str] = []
  for id, asset in assets.items():
    if (peg := asset.get('pegged_to')) is not None:
      target = peg['asset']
      if target == id:
        errors.append(f'[ASSET PEG ERROR] Asset "{id}" cannot be pegged to itself')
      elif target not in assets:
        errors.append(f'[ASSET PEG ERROR] Asset "{id}" is pegged to inexistent asset "{target}"')
  return errors

def asset_translations(assets: Mapping[str, Asset], asset_translations: Mapping[str, Mapping[str, str]]):
  errors: list[str] = []
  for platform, translations in asset_translations.items():
    for asset in translations.values():
      if asset not in assets:
        errors.append(f'[ASSET TRANSLATION ERROR] Asset translation "{platform}" has inexistent asset "{asset}"')
  return errors

def network_translations(platforms: Mapping[str, Platform], network_translations: Mapping[str, Mapping[str, str]]):
  errors: list[str] = []
  for platform, translations in network_translations.items():
    for network in translations.values():
      if network not in platforms:
        errors.append(f'[NETWORK TRANSLATION ERROR] Network translation "{platform}" has inexistent platform "{network}"')
  return errors


def platform_order(platforms: Mapping[str, Platform], base_folder: str):
  errors: list[str] = []
  order_file = _os.path.join(base_folder, 'data', 'platforms', 'order.txt')
  if not _os.path.exists(order_file):
    return ['[PLATFORM ORDER ERROR] Missing file "data/platforms/order.txt"']

  with open(order_file) as f:
    ordered_platforms = [line.strip() for line in f if line.strip()]

  unknown_platforms = [platform for platform in ordered_platforms if platform not in platforms]
  if unknown_platforms:
    unknown_platforms_display = ', '.join(unknown_platforms)
    errors.append(f'[PLATFORM ORDER ERROR] Unknown platform id(s) in "data/platforms/order.txt": {unknown_platforms_display}')

  duplicates = sorted({platform for platform in ordered_platforms if ordered_platforms.count(platform) > 1})
  if duplicates:
    duplicates_display = ', '.join(duplicates)
    errors.append(f'[PLATFORM ORDER ERROR] Duplicate platform id(s) in "data/platforms/order.txt": {duplicates_display}')

  missing_platforms = sorted(set(platforms.keys()) - set(ordered_platforms))
  if missing_platforms:
    missing_platforms_display = ', '.join(missing_platforms)
    errors.append(f'[PLATFORM ORDER ERROR] Missing platform id(s) in "data/platforms/order.txt": {missing_platforms_display}')

  return errors


def ranks(kind: str, items: Mapping[str, Mapping]):
  errors: list[str] = []
  ranks = [item.get('rank') for item in items.values()]
  if any(rank is None for rank in ranks):
    errors.append(f'[{kind} RANK ERROR] Missing rank value(s)')
    return errors
  sorted_items = sorted(items.values(), key=lambda item: item.get('rank')) # type: ignore
  ranks = [item['rank'] for item in sorted_items]
  expected = list(range(1, len(ranks) + 1))
  if ranks != expected:
    display = '\n'.join(f'{item["rank"]}: {item["display_name"]}' for item in sorted_items)
    errors.append(f'[{kind} RANK ERROR] Ranks must be consecutive starting at 1. Found:\n{display}')
  return errors

def spot_instruments(spot_instruments: Mapping[str, Mapping[str, Spot]], assets: Mapping[str, Asset]):
  errors: list[str] = []
  for platform, instruments in spot_instruments.items():
    for id, instrument in instruments.items():
      base, quote = instrument['base'], instrument['quote']
      if base not in assets:
        errors.append(f'[SPOT INSTRUMENT ERROR] Spot instrument "{id}" on "{platform}" has inexistent base asset "{base}"')
      if quote not in assets:
        errors.append(f'[SPOT INSTRUMENT ERROR] Spot instrument "{id}" on "{platform}" has inexistent quote asset "{quote}"')
  return errors

def perpetual_instruments(perpetual_instruments: Mapping[str, Mapping[str, Perpetual]], assets: Mapping[str, Asset]):
  errors: list[str] = []
  for platform, instruments in perpetual_instruments.items():
    for id, instrument in instruments.items():
      base, quote, settlement = instrument['base'], instrument['quote'], instrument['settlement']
      if base not in assets:
        errors.append(f'[PERPETUAL INSTRUMENT ERROR] Perpetual instrument "{id}" on "{platform}" has inexistent base asset "{base}"')
      if quote not in assets:
        errors.append(f'[PERPETUAL INSTRUMENT ERROR] Perpetual instrument "{id}" on "{platform}" has inexistent quote asset "{quote}"')
      if settlement not in assets:
        errors.append(f'[PERPETUAL INSTRUMENT ERROR] Perpetual instrument "{id}" on "{platform}" has inexistent settlement asset "{settlement}"')
  return errors

def debt_instruments(debt_instruments: Mapping[str, Mapping[str, Debt]], assets: Mapping[str, Asset]):
  errors: list[str] = []
  for platform, instruments in debt_instruments.items():
    for id, instrument in instruments.items():
      asset = instrument['asset']
      if asset not in assets:
        errors.append(f'[DEBT INSTRUMENT ERROR] Debt instrument "{id}" on "{platform}" has inexistent asset "{asset}"')
  return errors

def collateral_instruments(collateral_instruments: Mapping[str, Mapping[str, Collateral]], assets: Mapping[str, Asset]):
  errors: list[str] = []
  for platform, instruments in collateral_instruments.items():
    for id, instrument in instruments.items():
      asset = instrument['asset']
      if asset not in assets:
        errors.append(f'[COLLATERAL INSTRUMENT ERROR] Collateral instrument "{id}" on "{platform}" has inexistent asset "{asset}"')
  return errors

def pools(pools: Mapping[str, Mapping[str, Pool]], assets: Mapping[str, Asset]):
  errors: list[str] = []
  for platform, platform_pools in pools.items():
    for id, pool in platform_pools.items():
      for asset in pool['assets']:
        if asset not in assets:
          errors.append(f'[POOL ERROR] Pool "{id}" on "{platform}" has inexistent asset "{asset}"')
  return errors

def all(catalogue: Catalogue, base_folder: str):
  errors: list[str] = []
  errors.extend(ids('ASSET', catalogue.assets))
  errors.extend(ids('PLATFORM', catalogue.platforms))
  errors.extend(asset_icons(catalogue.assets, base_folder))
  errors.extend(platform_icons(catalogue.platforms, base_folder))
  errors.extend(platform_order(catalogue.platforms, base_folder))
  errors.extend(native_assets(catalogue.assets, catalogue.platforms))
  errors.extend(asset_pegs(catalogue.assets))
  errors.extend(platform_keys('ASSET TRANSLATION', catalogue.platforms, catalogue.asset_translations))
  errors.extend(platform_keys('NETWORK TRANSLATION', catalogue.platforms, catalogue.network_translations))
  errors.extend(platform_keys('SPOT INSTRUMENT', catalogue.platforms, catalogue.spot_instruments))
  errors.extend(platform_keys('PERPETUAL INSTRUMENT', catalogue.platforms, catalogue.perpetual_instruments))
  errors.extend(platform_keys('DEBT INSTRUMENT', catalogue.platforms, catalogue.debt_instruments))
  errors.extend(platform_keys('COLLATERAL INSTRUMENT', catalogue.platforms, catalogue.collateral_instruments))
  errors.extend(platform_keys('POOL', catalogue.platforms, catalogue.pools))
  errors.extend(platform_keys('SPAM', catalogue.platforms, catalogue.spam))
  errors.extend(asset_translations(catalogue.assets, catalogue.asset_translations))
  errors.extend(network_translations(catalogue.platforms, catalogue.network_translations))
  errors.extend(spot_instruments(catalogue.spot_instruments, catalogue.assets))
  errors.extend(perpetual_instruments(catalogue.perpetual_instruments, catalogue.assets))
  errors.extend(debt_instruments(catalogue.debt_instruments, catalogue.assets))
  errors.extend(collateral_instruments(catalogue.collateral_instruments, catalogue.assets))
  errors.extend(pools(catalogue.pools, catalogue.assets))
  return errors
