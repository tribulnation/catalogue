import os as _os
from .schema import Asset, Platform, Network, AssetTranslation, NetworkTranslation, Catalogue

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

def asset_translations(assets: dict[str, Asset], asset_translations: dict[str, list[AssetTranslation]]):
  errors: list[str] = []
  for platform, translations in asset_translations.items():
    for trans in translations:
      if trans['asset'] not in assets:
        errors.append(f'[ASSET TRANSLATION ERROR] Asset translation "{platform}" has inexistent asset "{trans.asset}"')
  return errors

def network_translations(networks: dict[str, Network], network_translations: dict[str, list[NetworkTranslation]]):
  errors: list[str] = []
  for platform, translations in network_translations.items():
    for trans in translations:
      if trans['network'] not in networks:
        errors.append(f'[NETWORK TRANSLATION ERROR] Network translation "{platform}" has inexistent network "{trans.network}"')
  return errors

def all(catalogue: Catalogue, base_folder: str):
  errors: list[str] = []
  errors.extend(asset_icons(catalogue.assets, base_folder))
  errors.extend(platform_icons(catalogue.platforms, base_folder))
  errors.extend(network_icons(catalogue.networks, base_folder))
  errors.extend(native_assets(catalogue.assets, catalogue.networks))
  errors.extend(asset_translations(catalogue.assets, catalogue.asset_translations))
  errors.extend(network_translations(catalogue.networks, catalogue.network_translations))
  return errors