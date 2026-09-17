"""Point each asset's `icon` field at `icons/asset/<id>.svg` once that file exists.

Sourcing agents write SVGs only; this wires them up in one pass, so several
agents never edit the same JSON file concurrently.

    python3 .agents/skills/batch_icons/scripts/wire_icons.py
"""
import os

from derive_icons import load, set_icon

def wire(root: str = '.') -> list[str]:
  done = []
  for name in sorted(os.listdir(os.path.join(root, 'data/assets'))):
    id = name[:-5]
    asset = load(id, root)
    icon = f'icons/asset/{id}.svg'
    if asset is None or asset.get('icon') or not os.path.exists(os.path.join(root, icon)):
      continue
    if set_icon(id, icon, root):
      done.append(id)
  return done

if __name__ == '__main__':
  done = wire()
  print(f'wired {len(done)}: ' + ', '.join(done) if done else 'nothing to wire')
