"""Require descriptions, URLs and provider IDs for assets added since a Git base.

A provider with no exact listing for the asset is acceptable only when the gap is
justified in `scripts/external_id_exceptions.json` under an `<asset>:<provider>`
key, saying what was searched and why nothing matched.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys


EXCEPTIONS_FILE = Path(__file__).with_name('external_id_exceptions.json')

# Crypto records must account for both providers: an ID or a justified gap each.
SEARCHED_PROVIDERS = ('coingecko', 'coinmarketcap')
CRYPTO_CATEGORIES = {'crypto', 'stablecoin', 'rwa'}


def nonblank(value: object) -> bool:
  """Return whether a value is a nonblank string."""
  return isinstance(value, str) and bool(value.strip())


def load_missing(file: Path = EXCEPTIONS_FILE) -> dict[str, str]:
  """Justified provider gaps, keyed '<asset>:<provider>' (mismatches use three parts)."""
  if not file.exists():
    return {}
  return {
    key: reason for key, reason in json.loads(file.read_text(encoding='utf-8')).items()
    if not key.startswith('_') and key.count(':') == 1
  }


def metadata_errors(
  asset: object, *, asset_id: str | None = None, missing: dict[str, str] | None = None
) -> list[str]:
  """Explain missing metadata without imposing requirements on legacy assets."""
  if not isinstance(asset, dict):
    return ['asset must be a JSON object']
  errors = []
  about = asset.get('about')
  if not isinstance(about, dict) or not nonblank(about.get('en')):
    errors.append('about.en must be a nonblank description')
  urls = asset.get('urls')
  if not isinstance(urls, dict) or not any(
    nonblank(key) and nonblank(value) for key, value in urls.items()
  ):
    errors.append('urls must contain at least one nonblank URL')
  external = asset.get('external')
  ids = {
    key for key, value in external.items() if nonblank(key) and nonblank(value)
  } if isinstance(external, dict) else set()
  asset_id = asset_id or asset.get('id')
  justified = {
    key.split(':', 1)[1]: reason for key, reason in (missing or {}).items()
    if key.split(':', 1)[0] == asset_id and nonblank(reason)
  }
  for provider in sorted(ids & set(justified)):
    errors.append(
      f'external.{provider} is set, so remove its stale justification from {EXCEPTIONS_FILE.name}'
    )
  if asset.get('category') in CRYPTO_CATEGORIES:
    for provider in SEARCHED_PROVIDERS:
      if provider not in ids and provider not in justified:
        errors.append(
          f'external.{provider} is missing: add the verified ID, or justify '
          f"'{asset_id}:{provider}' in {EXCEPTIONS_FILE.name}"
        )
  elif not ids and not justified:
    errors.append(
      'external must contain at least one nonblank external provider ID, or justify '
      f"'{asset_id}:<provider>' in {EXCEPTIONS_FILE.name}"
    )
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
  try:
    missing = load_missing(root / 'scripts' / EXCEPTIONS_FILE.name)
  except (OSError, ValueError) as error:
    print(f'Cannot read {EXCEPTIONS_FILE.name}: {error}', file=sys.stderr)
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
    for key, reason in sorted(missing.items()):
      if key.split(':', 1)[0] == asset_id:
        print(f'{path}: no {key.split(":", 1)[1]} listing - {reason}')
    errors.extend(
      f'{path}: {error}'
      for error in metadata_errors(asset, asset_id=asset_id, missing=missing)
    )
  if errors:
    print('\n'.join(errors), file=sys.stderr)
    return 1
  print(f'Checked {len(paths)} new assets: metadata requirements passed.')
  return 0


if __name__ == '__main__':
  sys.exit(main())
