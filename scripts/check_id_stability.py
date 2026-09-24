"""Fail when an asset or platform id published in the live data.zip is gone from the working tree.

Ids are the catalogue's contract with its consumers, which store them: they are never
renamed or deleted. A merged asset keeps its file with `replaced_by` pointing at the
surviving asset. See `validate.id_stability`.
"""

import argparse
import io
from pathlib import Path
import sys
import urllib.request
import zipfile

from tribulnation.catalogue.data.validate import id_stability

PUBLISHED = 'https://catalogue.tribulnation.com/data.zip'
KINDS = {'asset': 'assets', 'platform': 'platforms'}
"""Checked id kind -> folder holding one `<id>.json` per id"""


def ids_in_names(names: list[str]) -> dict[str, set[str]]:
  """Ids per kind from `<folder>/<id>.json` relative paths."""
  ids: dict[str, set[str]] = {kind: set() for kind in KINDS}
  for name in names:
    parts = name.split('/')
    if len(parts) != 2 or not parts[1].endswith('.json'):
      continue
    for kind, folder in KINDS.items():
      if parts[0] == folder:
        ids[kind].add(parts[1].removesuffix('.json'))
  return ids


def ids_in_archive(data: bytes) -> dict[str, set[str]]:
  """Ids per kind in the bytes of a `data.zip`."""
  with zipfile.ZipFile(io.BytesIO(data)) as zf:
    return ids_in_names(zf.namelist())


def ids_in_folder(folder: Path) -> dict[str, set[str]]:
  """Ids per kind in a data folder."""
  return ids_in_names([f'{name}/{file.name}' for name in KINDS.values() for file in (folder / name).glob('*.json')])


def read_baseline(source: str) -> dict[str, set[str]]:
  """Ids per kind from a data.zip URL, a local data.zip, or a local data folder."""
  if source.startswith(('http://', 'https://')):
    with urllib.request.urlopen(source, timeout=60) as response:
      return ids_in_archive(response.read())
  path = Path(source)
  if path.is_dir():
    return ids_in_folder(path)
  return ids_in_archive(path.read_bytes())


def main(argv: list[str] | None = None) -> int:
  """Compare the working tree's ids against the baseline and report removals."""
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--baseline', default=PUBLISHED, help='data.zip URL, local data.zip, or data folder (default: the published data.zip)')
  parser.add_argument('--data', default='data', help='Working-tree data folder')
  args = parser.parse_args(argv)
  errors = id_stability(ids_in_folder(Path(args.data)), read_baseline(args.baseline))
  for error in errors:
    print(error, file=sys.stderr)
  if errors:
    return 1
  print(f'No published ids removed (baseline: {args.baseline}).')
  return 0


if __name__ == '__main__':
  sys.exit(main())
