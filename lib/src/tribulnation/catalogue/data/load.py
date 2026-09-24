"""Load catalogue data from JSON files, in a folder or inside a `data.zip` archive."""

import io
from pathlib import Path
import logging
from typing import Iterator, TypeVar
from typing_extensions import Literal, Protocol
import zipfile

from pydantic import TypeAdapter, ValidationError

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
T = TypeVar('T')
logger = logging.getLogger('tribulnation.catalogue')

def _extra(strict: bool) -> _Extra:
  """Resolve the pydantic `extra` mode."""
  return 'forbid' if strict else 'ignore'

class Folder(Protocol):
  """A readable directory: a `pathlib.Path` or a `zipfile.Path` inside an archive."""
  @property
  def name(self) -> str: ...
  def iterdir(self) -> Iterator['Folder']: ...
  def is_dir(self) -> bool: ...
  def is_file(self) -> bool: ...
  def read_bytes(self) -> bytes: ...
  def __truediv__(self, other: str, /) -> 'Folder': ...

def json_files(folder: Folder) -> Iterator[tuple[str, bytes]]:
  """Yield `(stem, content)` for every `*.json` file directly in `folder`; nothing if it is missing."""
  if not folder.is_dir():
    return
  for file in folder.iterdir():
    if file.is_file() and file.name.endswith('.json'):
      yield file.name.removesuffix('.json'), file.read_bytes()

def records(folder: Folder, adapter: TypeAdapter[T], *, strict: bool, skip_invalid: bool) -> dict[str, T]:
  """Validate every `*.json` file in `folder`, keyed by file stem.

  Args:
    folder: Folder holding the files.
    adapter: Validator of one file.
    strict: Reject unknown fields.
    skip_invalid: Log and skip files that fail validation instead of raising, so a client
      reading newer live data (e.g. a new enum value) keeps every record it understands.
  """
  extra = _extra(strict)
  out: dict[str, T] = {}
  for stem, content in json_files(folder):
    try:
      out[stem] = adapter.validate_json(content, extra=extra)
    except ValidationError as e:
      if not skip_invalid:
        raise
      logger.warning('Skipping catalogue file %s/%s.json: %d validation error(s)', folder.name, stem, e.error_count())
  return out

def assets(folder: Folder, *, strict: bool = False, skip_invalid: bool = False) -> dict[str, Asset]:
  """Load all asset definitions from a folder."""
  return records(folder, _asset_adapter, strict=strict, skip_invalid=skip_invalid)

def assets_order(file: Folder) -> list[str]:
  """Load asset display order."""
  return [id for line in file.read_bytes().decode().splitlines() if (id := line.strip())]

def platforms(folder: Folder, *, strict: bool = False, skip_invalid: bool = False) -> dict[str, Platform]:
  """Load all platform definitions from a folder."""
  return records(folder, _platform_adapter, strict=strict, skip_invalid=skip_invalid)

def platforms_order(file: Folder) -> list[str]:
  """Load platform display order."""
  return [id for line in file.read_bytes().decode().splitlines() if (id := line.strip())]

def network_translations(folder: Folder, *, strict: bool = False, skip_invalid: bool = False) -> dict[str, dict[str, str]]:
  """Load network translation mappings (`platform -> native network -> platform id`)."""
  return records(folder, _network_translation_adapter, strict=strict, skip_invalid=skip_invalid)

def asset_translations(folder: Folder, *, strict: bool = False, skip_invalid: bool = False) -> dict[str, dict[str, str]]:
  """Load asset translation mappings (`platform -> native id -> asset id`)."""
  return records(folder, _asset_translation_adapter, strict=strict, skip_invalid=skip_invalid)

def spot_instruments(folder: Folder, *, strict: bool = False, skip_invalid: bool = False) -> dict[str, dict[str, Spot]]:
  """Load spot instrument definitions."""
  return records(folder, _spot_instruments_adapter, strict=strict, skip_invalid=skip_invalid)

def perpetual_instruments(folder: Folder, *, strict: bool = False, skip_invalid: bool = False) -> dict[str, dict[str, Perpetual]]:
  """Load perpetual instrument definitions."""
  return records(folder, _perpetual_instruments_adapter, strict=strict, skip_invalid=skip_invalid)

def debt_instruments(folder: Folder, *, strict: bool = False, skip_invalid: bool = False) -> dict[str, dict[str, Debt]]:
  """Load debt instrument definitions."""
  return records(folder, _debt_instruments_adapter, strict=strict, skip_invalid=skip_invalid)

def spam(folder: Folder, *, strict: bool = False, skip_invalid: bool = False) -> dict[str, dict[str, SpamAddress]]:
  """Load spam address records."""
  return records(folder, _spam_adapter, strict=strict, skip_invalid=skip_invalid)

def pools(folder: Folder, *, strict: bool = False, skip_invalid: bool = False) -> dict[str, dict[str, Pool]]:
  """Load pool definitions."""
  return records(folder, _pools_adapter, strict=strict, skip_invalid=skip_invalid)

def all(folder: Path | str | Folder, *, strict: bool = False, skip_invalid: bool = False) -> Catalogue:
  """Load the full catalogue from a data folder (or a `zipfile.Path` at the root of `data.zip`).

  Args:
    folder: The data folder.
    strict: Reject unknown fields.
    skip_invalid: Log and skip files that fail validation instead of raising.
  """
  if isinstance(folder, str):
    folder = Path(folder)
  kw = dict(strict=strict, skip_invalid=skip_invalid)
  return Catalogue(
    assets=assets(folder / 'assets', **kw),
    platforms=platforms(folder / 'platforms', **kw),
    platforms_order=platforms_order(folder / 'platforms' / 'order.txt'),
    network_translations=network_translations(folder / 'network_translations', **kw),
    asset_translations=asset_translations(folder / 'asset_translations', **kw),
    spot_instruments=spot_instruments(folder / 'instruments' / 'spot', **kw),
    perpetual_instruments=perpetual_instruments(folder / 'instruments' / 'perpetual', **kw),
    debt_instruments=debt_instruments(folder / 'instruments' / 'debt', **kw),
    pools=pools(folder / 'instruments' / 'pools', **kw),
    spam=spam(folder / 'spam', **kw),
  )

def archive(data: bytes, *, strict: bool = False, skip_invalid: bool = False) -> Catalogue:
  """Load the full catalogue from the bytes of a `data.zip` archive, without extracting it."""
  with zipfile.ZipFile(io.BytesIO(data)) as zf:
    return all(zipfile.Path(zf), strict=strict, skip_invalid=skip_invalid)
