"""Require descriptions, URLs and provider IDs for assets added since a Git base."""

import argparse
import json
from pathlib import Path
import subprocess
import sys


# Missing supported pricing identities are tracked; other metadata remains required.
EXTERNAL_ID_EXCEPTIONS = {
  'coinbase-50-index': 'https://github.com/tribulnation/catalogue/issues/152',
  'minteo-copm': 'https://github.com/tribulnation/catalogue/issues/130',
}


def nonblank(value: object) -> bool:
  """Return whether a value is a nonblank string."""
  return isinstance(value, str) and bool(value.strip())


def metadata_errors(asset: object, *, asset_id: str | None = None) -> list[str]:
  """Explain missing metadata without imposing requirements on legacy assets."""
  if not isinstance(asset, dict):
    return ['asset must be a JSON object']
  errors = []
  about = asset.get('about')
  if not isinstance(about, dict) or not nonblank(about.get('en')):
    errors.append('about.en must be a nonblank description')
  for field, label in [('urls', 'URL'), ('external', 'external provider ID')]:
    values = asset.get(field)
    if not isinstance(values, dict) or not any(
      nonblank(key) and nonblank(value) for key, value in values.items()
    ):
      if (
        field == 'external'
        and asset_id in EXTERNAL_ID_EXCEPTIONS
        and asset.get('id') == asset_id
      ):
        continue
      errors.append(f'{field} must contain at least one nonblank {label}')
  return errors


def git(*args: str) -> str:
  """Run a read-only Git command in the caller's repository."""
  return subprocess.run(
    ['git', *args],
    check=True,
    capture_output=True,
    text=True,
  ).stdout


def main() -> int:
  """Check added asset files and return a failing status with localized errors."""
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--base', required=True, help='Git commit or ref for the PR base')
  args = parser.parse_args()
  try:
    root = Path(git('rev-parse', '--show-toplevel').strip())
    base = git(
      'rev-parse', '--verify', '--end-of-options', f'{args.base}^{{commit}}'
    ).strip()
    added = git(
      '-C',
      str(root),
      'diff',
      '--name-only',
      '--diff-filter=A',
      '--no-renames',
      '-z',
      base,
      '--',
      'data/assets/*.json',
    ).split('\0')
  except (OSError, subprocess.CalledProcessError) as error:
    detail = (
      error.stderr.strip()
      if isinstance(error, subprocess.CalledProcessError)
      else str(error)
    )
    print(f'Cannot compare new assets against {args.base!r}: {detail}', file=sys.stderr)
    return 2
  errors = []
  paths = [path for path in added if path]
  for path in paths:
    try:
      asset = json.loads((root / path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
      errors.append(f'{path}: cannot read asset JSON: {error}')
      continue
    asset_id = Path(path).stem
    if (
      isinstance(asset, dict)
      and asset.get('id') == asset_id
      and asset_id in EXTERNAL_ID_EXCEPTIONS
    ):
      if any(error.startswith('external ') for error in metadata_errors(asset)):
        print(
          f'{path}: external ID exception tracked at {EXTERNAL_ID_EXCEPTIONS[asset_id]}'
        )
    errors.extend(
      f'{path}: {error}' for error in metadata_errors(asset, asset_id=asset_id)
    )
  if errors:
    print('\n'.join(errors), file=sys.stderr)
    return 1
  print(f'Checked {len(paths)} new assets: metadata requirements passed.')
  return 0


if __name__ == '__main__':
  sys.exit(main())
