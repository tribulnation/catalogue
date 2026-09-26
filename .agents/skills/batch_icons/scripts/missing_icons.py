"""List catalogue assets with no usable icon, classified by how to get one.

    python3 .agents/skills/batch_icons/scripts/missing_icons.py [--json]
"""
import json
import os
import sys

from derive_icons import AAVE_PREFIXES, BSTOCK_SUFFIX, SHARED_PREFIXES, underlying_of

def missing(root: str = '.'):
  out = []
  folder = os.path.join(root, 'data/assets')
  for name in sorted(os.listdir(folder)):
    asset = json.load(open(os.path.join(folder, name), encoding='utf-8'))
    icon = asset.get('icon')
    if icon and os.path.exists(os.path.join(root, icon)):
      continue
    id = asset['id']
    kind = 'source'
    if id.endswith(BSTOCK_SUFFIX):
      kind = 'bstock'
    elif any(id.startswith(p) for p in AAVE_PREFIXES):
      kind = 'aave-frame'
    elif underlying_of(id, SHARED_PREFIXES, root) is not None:
      kind = 'shared'
    out.append({'id': id, 'name': asset.get('display_name'), 'symbol': asset.get('symbol'), 'kind': kind})
  return out

if __name__ == '__main__':
  rows = missing()
  if '--json' in sys.argv:
    print(json.dumps(rows, indent=1))
  else:
    for kind in ('bstock', 'aave-frame', 'shared', 'source'):
      group = [r for r in rows if r['kind'] == kind]
      print(f'\n{kind} ({len(group)}):')
      for r in group:
        print(f"  {r['id']}  ({r['symbol']})")
    print(f'\ntotal: {len(rows)}')
