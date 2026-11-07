"""The catalogue data the checks compare against, read straight from `data/`.

Only plain JSON reads: the checks run in whatever environment the caller has, with
no dependency on the `tribulnation.catalogue` package.
"""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Literal

Kind = Literal['spot', 'perp']
MarketKey = tuple[str, str]
"""`(exchange ID, market ID)`, which is how the catalogue keys an instrument."""


@dataclass
class Catalogue:
  """The parts of the catalogue the checks read."""

  assets: dict[str, dict[str, Any]] = field(default_factory=dict)
  """Asset records by canonical ID."""
  instruments: dict[str, dict[MarketKey, dict[str, Any]]] = field(default_factory=dict)
  """Per platform, its spot and perpetual instruments; each record carries `kind` and `id`."""
  asset_translations: dict[str, dict[str, str]] = field(default_factory=dict)
  network_translations: dict[str, dict[str, str]] = field(default_factory=dict)
  spam: dict[str, set[str]] = field(default_factory=dict)
  """Known spam addresses per platform, lowercased."""


def _json_dir(directory: Path) -> dict[str, Any]:
  """Every `<name>.json` in a directory, by name."""
  if not directory.is_dir():
    return {}
  return {path.stem: json.loads(path.read_text(encoding='utf-8')) for path in sorted(directory.glob('*.json'))}


def load(data: Path) -> Catalogue:
  """
  Read the catalogue from a data directory.

  Args:
    data: The `data/` directory of a catalogue checkout.
  """
  catalogue = Catalogue(
    assets=_json_dir(data / 'assets'),
    asset_translations=_json_dir(data / 'asset_translations'),
    network_translations=_json_dir(data / 'network_translations'),
    spam={platform: {address.lower() for address in rows} for platform, rows in _json_dir(data / 'spam').items()},
  )
  for kind, folder in (('spot', 'spot'), ('perp', 'perpetual')):
    for platform, rows in _json_dir(data / 'instruments' / folder).items():
      keyed = catalogue.instruments.setdefault(platform, {})
      for id, instrument in rows.items():
        keyed[(instrument.get('exchange', ''), id)] = {**instrument, 'kind': kind, 'id': id}
  return catalogue
