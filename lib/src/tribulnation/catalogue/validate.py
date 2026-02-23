import os as _os
from .schema import Asset, Platform, Network, Catalogue, Spot, Perpetual

def asset_icons(assets: dict[str, Asset], base_folder: str):
  errors: list[str] = []
  for id, asset in assets.items():
    if (icon := asset.get('icon')) is not None:
      if not _os.path.exists(_os.path.join(base_folder, icon)):
        errors.append(f'[ASSET ICON ERROR] Asset "{id}" has inexistent icon "{icon}"')
  return errors

def platform_icons(platforms: dict[str, Platform], base_folder: str):
  errors: list[str] = []
  for id, platform in platforms.items():
    if (icon := platform.get('icon')) is not None:
      if not _os.path.exists(_os.path.join(base_folder, icon)):
        errors.append(f'[PLATFORM ICON ERROR] Platform "{id}" has inexistent icon "{icon}"')
  return errors

def network_icons(networks: dict[str, Network], base_folder: str):
  errors: list[str] = []
  for id, network in networks.items():
    if (icon := network.get('icon')) is not None:
      if not _os.path.exists(_os.path.join(base_folder, icon)):
        errors.append(f'[NETWORK ICON ERROR] Network "{id}" has inexistent icon "{icon}"')
  return errors

def native_assets(assets: dict[str, Asset], networks: dict[str, Network]):
  errors: list[str] = []
  for id, network in networks.items():
    if (asset := network.get('native_asset')) is not None:
      if asset not in assets:
        errors.append(f'[NATIVE ASSET ERROR] Network "{id}" has inexistent native asset "{asset}"')
  return errors

def asset_translations(assets: dict[str, Asset], asset_translations: dict[str, dict[str, str]]):
  errors: list[str] = []
  for platform, translations in asset_translations.items():
    for asset in translations.values():
      if asset not in assets:
        errors.append(f'[ASSET TRANSLATION ERROR] Asset translation "{platform}" has inexistent asset "{asset}"')
  return errors

def network_translations(networks: dict[str, Network], network_translations: dict[str, dict[str, str]]):
  errors: list[str] = []
  for platform, translations in network_translations.items():
    for network in translations.values():
      if network not in networks:
        errors.append(f'[NETWORK TRANSLATION ERROR] Network translation "{platform}" has inexistent network "{network}"')
  return errors

def ranks(kind: str, items: dict[str, dict]):
  errors: list[str] = []
  ranks = [item.get('rank') for item in items.values()]
  if any(rank is None for rank in ranks):
    errors.append(f'[{kind} RANK ERROR] Missing rank value(s)')
    return errors
  sorted_items = sorted(items.values(), key=lambda item: item.get('rank'))
  ranks = [item['rank'] for item in sorted_items]
  expected = list(range(1, len(ranks) + 1))
  if ranks != expected:
    display = '\n'.join(f'{item["rank"]}: {item["display_name"]}' for item in sorted_items)
    errors.append(f'[{kind} RANK ERROR] Ranks must be consecutive starting at 1. Found:\n{display}')
  return errors

def spot_instruments(spot_instruments: dict[str, dict[str, Spot]], assets: dict[str, Asset]):
  errors: list[str] = []
  for platform, instruments in spot_instruments.items():
    for instrument in instruments.values():
      base, quote, id = instrument['base'], instrument['quote'], instrument['id']
      if base not in assets:
        errors.append(f'[SPOT INSTRUMENT ERROR] Spot instrument "{id}" on "{platform}" has inexistent base asset "{base}"')
      if quote not in assets:
        errors.append(f'[SPOT INSTRUMENT ERROR] Spot instrument "{id}" on "{platform}" has inexistent quote asset "{quote}"')
  return errors

def perpetual_instruments(perpetual_instruments: dict[str, dict[str, Perpetual]], assets: dict[str, Asset]):
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
  errors.extend(native_assets(catalogue.assets, catalogue.networks))
  errors.extend(asset_translations(catalogue.assets, catalogue.asset_translations))
  errors.extend(network_translations(catalogue.networks, catalogue.network_translations))
  errors.extend(ranks('ASSET', catalogue.assets))
  errors.extend(ranks('PLATFORM', catalogue.platforms))
  errors.extend(ranks('NETWORK', catalogue.networks))
  errors.extend(spot_instruments(catalogue.spot_instruments, catalogue.assets))
  errors.extend(perpetual_instruments(catalogue.perpetual_instruments, catalogue.assets))
  return errors
