from pathlib import Path
import sys

from tribulnation.catalogue.data import validate, load

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maintenance import catalogue as maintenance_catalogue  # noqa: E402
from maintenance.external import duplicates  # noqa: E402

catalogue = load.all('data', strict=True)
errors = validate.all(catalogue, '.')
errors += [f'[DUPLICATE EXTERNAL ID] {f["summary"]}' for f in duplicates(maintenance_catalogue.load(Path('data')))]
if errors:
  for error in errors:
    print(error, file=sys.stderr)
  sys.exit(1)
else:
  print('No errors found. Loaded:')
  print(f'> Assets: {len(catalogue.assets)}')
  print(f'> Platforms: {len(catalogue.platforms)}')
  print(f'> Network translations: {len(catalogue.network_translations)} platforms')
  print(f'> Asset translations: {len(catalogue.asset_translations)} platforms')
  print(f'> Protocols: {len(catalogue.protocols)}')
