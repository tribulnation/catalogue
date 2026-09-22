"""Build the icons that follow mechanically from another asset's icon.

Two kinds:

- **Aave receipt tokens** (`aave-<x>`, `wrapped-aave-<x>`) get the Aave gradient
  frame from `.agents/skills/create_aave_icon`, wrapping `<x>`'s glyph.
- **Wrapped / pegged / bridged representations** (`wrapped-<x>`, `binance-peg-<x>`,
  `bridged-<x>`, ...) share `<x>`'s icon file: the `icon` field points at it
  instead of duplicating the artwork. The repo already does this elsewhere
  (`usual` and `frax-usd` are each referenced by two assets).

    python3 .agents/skills/batch_icons/scripts/derive_icons.py          # plan only
    python3 .agents/skills/batch_icons/scripts/derive_icons.py --apply
"""
import collections
import json
import os
import sys

import icon_svg

AAVE_PREFIXES = ('wrapped-aave-', 'aave-')
SHARED_PREFIXES = (
  'binance-peg-', 'synapse-bridged-', 'avalanche-bridged-', 'bttc-bridged-',
  'orbit-bridge-', 'onesec-', 'bridged-', 'wrapped-',
)

TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <defs>
    <linearGradient id="aave" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#B6509E"/>
      <stop offset="100%" stop-color="#2EBAC6"/>
    </linearGradient>
    <mask id="frame">
      <rect width="200" height="200" fill="white"/>
      <circle cx="100" cy="100" r="88" fill="black"/>
    </mask>
    <clipPath id="inner">
      <circle cx="100" cy="100" r="82"/>
    </clipPath>
  </defs>
  <rect width="200" height="200" fill="url(#aave)" mask="url(#frame)"/>
  <circle cx="100" cy="100" r="82" fill="white"/>
  <g clip-path="url(#inner)">
  <svg{extra} x="18" y="18" width="164" height="164" viewBox="{viewbox}">
{body}
  </svg>
  </g>
</svg>
'''

def load(id: str, root: str = '.'):
  path = os.path.join(root, 'data/assets', f'{id}.json')
  if not os.path.exists(path):
    return None
  return json.load(open(path, encoding='utf-8'), object_pairs_hook=collections.OrderedDict)

def icon_of(id: str, root: str = '.') -> str | None:
  asset = load(id, root)
  if asset is None:
    return None
  icon = asset.get('icon')
  return icon if icon and os.path.exists(os.path.join(root, icon)) else None

def underlying_of(id: str, prefixes, root: str = '.') -> str | None:
  """The asset a derived id is built on, if that asset exists and has an icon.

  Either the id carries one of `prefixes`, or the asset names what it tracks in
  `pegged_to` — the latter covers representations whose id is not built from the
  underlying's, such as Bitget's Reality rTokens (`<equity>-rtoken`, rUNH).
  """
  for prefix in prefixes:
    if id.startswith(prefix):
      base = id[len(prefix):]
      if icon_of(base, root):
        return base
  asset = load(id, root)
  base = (asset or {}).get('pegged_to', {}).get('asset')
  if base and icon_of(base, root):
    return base
  return None

def set_icon(id: str, icon: str, root: str = '.') -> bool:
  asset = load(id, root)
  if asset is None or asset.get('icon') == icon:
    return False
  out = collections.OrderedDict()
  for key, value in asset.items():
    if key == 'urls' and 'icon' not in asset:
      out['icon'] = icon
    out[key] = icon if key == 'icon' else value
  out.setdefault('icon', icon)
  with open(os.path.join(root, 'data/assets', f'{id}.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, ensure_ascii=True)
    f.write('\n')
  return True

def aave_frame(target: str, underlying: str, root: str = '.') -> str:
  source = icon_of(underlying, root)
  if source is None:
    return f'SKIP {target}: {underlying} has no icon yet'
  svg = icon_svg.flatten_styles(open(os.path.join(root, source), encoding='utf-8').read())
  viewbox, body, extra = icon_svg.split_root(svg)
  markup = TEMPLATE.format(
    viewbox=viewbox, extra=extra,
    body='\n'.join(('  ' + line) if line.strip() else line for line in body.split('\n')),
  )
  path = f'icons/asset/{target}.svg'
  open(os.path.join(root, path), 'w', encoding='utf-8').write(markup)
  set_icon(target, path, root)
  return f'FRAME {target} <- {source}'

def share(target: str, underlying: str, root: str = '.') -> str:
  source = icon_of(underlying, root)
  if source is None:
    return f'SKIP {target}: {underlying} has no icon yet'
  own = os.path.join(root, f'icons/asset/{target}.svg')
  if os.path.exists(own):
    os.remove(own)
  set_icon(target, source, root)
  return f'SHARE {target} -> {source}'

def run(apply: bool = False, root: str = '.'):
  from missing_icons import missing
  lines = []
  # shared first: an Aave frame may be built on an asset that just got one
  for kind, prefixes, build in (('shared', SHARED_PREFIXES, share), ('aave-frame', AAVE_PREFIXES, aave_frame)):
    for row in missing(root):
      if row['kind'] != kind:
        continue
      underlying = underlying_of(row['id'], prefixes, root)
      if underlying is None:
        # for Aave ids the underlying may exist but still be icon-less
        underlying = next((row['id'][len(p):] for p in prefixes if row['id'].startswith(p)), None)
        lines.append(f"SKIP {row['id']}: {underlying} has no icon yet")
        continue
      lines.append(build(row['id'], underlying, root) if apply else f"WOULD {kind} {row['id']} <- {underlying}")
  return lines

if __name__ == '__main__':
  for line in run(apply='--apply' in sys.argv):
    print(line)
