"""Load catalogue data from JSON files."""

from collections import defaultdict
from pathlib import Path
from typing_extensions import Literal

from pydantic import TypeAdapter

from .schema import Asset, Platform, Spot, Perpetual, Debt, SpamAddress, Pool
from .main import Catalogue

_asset_adapter = TypeAdapter(Asset)
_platform_adapter = TypeAdapter(Platform)
_asset_translation_adapter = TypeAdapter(dict[str, str])
_network_translation_adapter = TypeAdapter(dict[str, str])
_spot_instruments_adapter = TypeAdapter(dict[str, Spot])
_perpetual_instruments_adapter = TypeAdapter(dict[str, Perpetual])
_debt_instruments_adapter = TypeAdapter(dict[str, Debt])
_spam_adapter = TypeAdapter(dict[str, SpamAddress])
_pools_adapter = TypeAdapter(dict[str, Pool])

_Extra = Literal['forbid', 'ignore']

def _extra(strict: bool) -> _Extra:
  """Resolve the pydantic `extra` mode."""
  return 'forbid' if strict else 'ignore'

def assets(folder: Path, *, strict: bool = False) -> dict[str, Asset]:
  """Load all asset definitions from a folder."""
  extra = _extra(strict)
  assets: dict[str, Asset] = {}
  for file in folder.glob('*.json'):
    id = file.stem
    assets[id] = _asset_adapter.validate_json(file.read_bytes(), extra=extra)
  return assets

def assets_order(file: Path) -> list[str]:
  """Load asset display order."""
  return [id for line in file.read_text().splitlines() if (id := line.strip())]

def platforms(folder: Path, *, strict: bool = False) -> dict[str, Platform]:
  """Load all platform definitions from a folder."""
  extra = _extra(strict)
  platforms: dict[str, Platform] = {}
  for file in folder.glob('*.json'):
    id = file.stem
    platforms[id] = _platform_adapter.validate_json(file.read_bytes(), extra=extra)
  return platforms

def platforms_order(file: Path) -> list[str]:
  """Load platform display order."""
  return [id for line in file.read_text().splitlines() if (id := line.strip())]

def network_translations(folder: Path, *, strict: bool = False) -> dict[str, dict[str, str]]:
  """Load network translation mappings."""
  extra = _extra(strict)
  network_translations = defaultdict[str, dict[str, str]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    network_translations[platform].update(_network_translation_adapter.validate_json(file.read_bytes(), extra=extra))
  return dict(network_translations)

def asset_translations(folder: Path, *, strict: bool = False) -> dict[str, dict[str, str]]:
  """Load asset translation mappings."""
  extra = _extra(strict)
  asset_translations = defaultdict[str, dict[str, str]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    asset_translations[platform].update(_asset_translation_adapter.validate_json(file.read_bytes(), extra=extra))
  return dict(asset_translations)

def spot_instruments(folder: Path, *, strict: bool = False) -> dict[str, dict[str, Spot]]:
  """Load spot instrument definitions."""
  extra = _extra(strict)
  spot_instruments = defaultdict[str, dict[str, Spot]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    spot_instruments[platform].update(_spot_instruments_adapter.validate_json(file.read_bytes(), extra=extra))
  return dict(spot_instruments)

def perpetual_instruments(folder: Path, *, strict: bool = False) -> dict[str, dict[str, Perpetual]]:
  """Load perpetual instrument definitions."""
  extra = _extra(strict)
  perpetual_instruments = defaultdict[str, dict[str, Perpetual]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    perpetual_instruments[platform].update(_perpetual_instruments_adapter.validate_json(file.read_bytes(), extra=extra))
  return dict(perpetual_instruments)

def debt_instruments(folder: Path, *, strict: bool = False) -> dict[str, dict[str, Debt]]:
  """Load debt instrument definitions."""
  extra = _extra(strict)
  debt_instruments = defaultdict[str, dict[str, Debt]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    debt_instruments[platform].update(_debt_instruments_adapter.validate_json(file.read_bytes(), extra=extra))
  return dict(debt_instruments)

def spam(folder: Path, *, strict: bool = False) -> dict[str, dict[str, SpamAddress]]:
  """Load spam address records."""
  extra = _extra(strict)
  spam = defaultdict[str, dict[str, SpamAddress]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    spam[platform].update(_spam_adapter.validate_json(file.read_bytes(), extra=extra))
  return dict(spam)

def pools(folder: Path, *, strict: bool = False) -> dict[str, dict[str, Pool]]:
  """Load pool definitions."""
  extra = _extra(strict)
  pools = defaultdict[str, dict[str, Pool]](dict)
  for file in folder.glob('*.json'):
    platform = file.stem
    pools[platform].update(_pools_adapter.validate_json(file.read_bytes(), extra=extra))
  return dict(pools)

def all(folder: Path | str, *, strict: bool = False) -> Catalogue:
  """Load the full catalogue from a data folder."""
  folder = Path(folder)
  return Catalogue(
    assets=assets(folder / 'assets', strict=strict),
    platforms=platforms(folder / 'platforms', strict=strict),
    platforms_order=platforms_order(folder / 'platforms' / 'order.txt'),
    network_translations=network_translations(folder / 'network_translations', strict=strict),
    asset_translations=asset_translations(folder / 'asset_translations', strict=strict),
    spot_instruments=spot_instruments(folder / 'instruments' / 'spot', strict=strict),
    perpetual_instruments=perpetual_instruments(folder / 'instruments' / 'perpetual', strict=strict),
    debt_instruments=debt_instruments(folder / 'instruments' / 'debt', strict=strict),
    pools=pools(folder / 'instruments' / 'pools', strict=strict),
    spam=spam(folder / 'spam', strict=strict),
  )
