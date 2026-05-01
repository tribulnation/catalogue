from tribulnation.catalogue import validate, load

catalogue = load.all('data')
errors = validate.all(catalogue, '.')
if errors:
  import sys
  for error in errors:
    print(error, file=sys.stderr)
  sys.exit(1)
else:
  print('No errors found. Loaded:')
  print(f'> Assets: {len(catalogue.assets)}')
  print(f'> Platforms: {len(catalogue.platforms)}')
  print(f'> Network translations: {len(catalogue.network_translations)} platforms')
  print(f'> Asset translations: {len(catalogue.asset_translations)} platforms')