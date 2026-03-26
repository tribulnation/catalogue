import os as _os
from typing import Mapping
from .schema import Asset, Platform, Network, Catalogue, Spot, Perpetual

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

def network_icons(networks: Mapping[str, Network], base_folder: str):
  errors: list[str] = []
  for id, network in networks.items():
    if (icon := network.get('icon')) is not None:
      if not _os.path.exists(_os.path.join(base_folder, icon)):
        errors.append(f'[NETWORK ICON ERROR] Network "{id}" has inexistent icon "{icon}"')
  return errors

def native_assets(assets: Mapping[str, Asset], networks: Mapping[str, Network]):
  errors: list[str] = []
  for id, network in networks.items():
    if (asset := network.get('native_asset')) is not None:
      if asset not in assets:
        errors.append(f'[NATIVE ASSET ERROR] Network "{id}" has inexistent native asset "{asset}"')
  return errors

def asset_translations(assets: Mapping[str, Asset], asset_translations: Mapping[str, Mapping[str, str]]):
  errors: list[str] = []
  for platform, translations in asset_translations.items():
    for asset in translations.values():
      if asset not in assets:
        errors.append(f'[ASSET TRANSLATION ERROR] Asset translation "{platform}" has inexistent asset "{asset}"')
  return errors

def network_translations(networks: Mapping[str, Network], network_translations: Mapping[str, Mapping[str, str]]):
  errors: list[str] = []
  for platform, translations in network_translations.items():
    for network in translations.values():
      if network not in networks:
        errors.append(f'[NETWORK TRANSLATION ERROR] Network translation "{platform}" has inexistent network "{network}"')
  return errors

def asset_order(assets: Mapping[str, Asset], base_folder: str):
  errors: list[str] = []
  order_file = _os.path.join(base_folder, 'data', 'assets', 'order.txt')
  if not _os.path.exists(order_file):
    return ['[ASSET ORDER ERROR] Missing file "data/assets/order.txt"']

  with open(order_file) as f:
    ordered_assets = [line.strip() for line in f if line.strip()]

  unknown_assets = [asset for asset in ordered_assets if asset not in assets]
  if unknown_assets:
    unknown_assets_display = ', '.join(unknown_assets)
    errors.append(f'[ASSET ORDER ERROR] Unknown asset id(s) in "data/assets/order.txt": {unknown_assets_display}')

  duplicates = sorted({asset for asset in ordered_assets if ordered_assets.count(asset) > 1})
  if duplicates:
    duplicates_display = ', '.join(duplicates)
    errors.append(f'[ASSET ORDER ERROR] Duplicate asset id(s) in "data/assets/order.txt": {duplicates_display}')

  missing_assets = sorted(set(assets.keys()) - set(ordered_assets))
  if missing_assets:
    missing_assets_display = ', '.join(missing_assets)
    errors.append(f'[ASSET ORDER ERROR] Missing asset id(s) in "data/assets/order.txt": {missing_assets_display}')

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
    for instrument in instruments.values():
      base, quote, id = instrument['base'], instrument['quote'], instrument['id']
      if base not in assets:
        errors.append(f'[SPOT INSTRUMENT ERROR] Spot instrument "{id}" on "{platform}" has inexistent base asset "{base}"')
      if quote not in assets:
        errors.append(f'[SPOT INSTRUMENT ERROR] Spot instrument "{id}" on "{platform}" has inexistent quote asset "{quote}"')
  return errors

def perpetual_instruments(perpetual_instruments: Mapping[str, Mapping[str, Perpetual]], assets: Mapping[str, Asset]):
  errors: list[str] = []
  for platform, instruments in perpetual_instruments.items():
    for instrument in instruments.values():
      base, quote, settlement, id = instrument['base'], instrument['quote'], instrument['settlement'], instrument['id']
      if base not in assets:
        errors.append(f'[PERPETUAL INSTRUMENT ERROR] Perpetual instrument "{id}" on "{platform}" has inexistent base asset "{base}"')
      if quote not in assets:
        errors.append(f'[PERPETUAL INSTRUMENT ERROR] Perpetual instrument "{id}" on "{platform}" has inexistent quote asset "{quote}"')
      if settlement not in assets:
        errors.append(f'[PERPETUAL INSTRUMENT ERROR] Perpetual instrument "{id}" on "{platform}" has inexistent settlement asset "{settlement}"')
  return errors

def all(catalogue: Catalogue, base_folder: str):
  errors: list[str] = []
  errors.extend(asset_icons(catalogue.assets, base_folder))
  errors.extend(platform_icons(catalogue.platforms, base_folder))
  errors.extend(network_icons(catalogue.networks, base_folder))
  errors.extend(asset_order(catalogue.assets, base_folder))
  errors.extend(platform_order(catalogue.platforms, base_folder))
  errors.extend(native_assets(catalogue.assets, catalogue.networks))
  errors.extend(asset_translations(catalogue.assets, catalogue.asset_translations))
  errors.extend(network_translations(catalogue.networks, catalogue.network_translations))
  errors.extend(ranks('NETWORK', catalogue.networks))
  errors.extend(spot_instruments(catalogue.spot_instruments, catalogue.assets))
  errors.extend(perpetual_instruments(catalogue.perpetual_instruments, catalogue.assets))
  return errors
