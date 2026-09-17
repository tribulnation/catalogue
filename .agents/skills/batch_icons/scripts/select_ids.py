"""Pick which assets a report covers: an explicit list, or what changed in git."""
import json
import os
import subprocess

def changed_since(ref: str, root: str = '.') -> list[str]:
  out = subprocess.run(
    ['git', 'diff', '--name-only', ref, '--', 'data/assets'],
    cwd=root, capture_output=True, text=True, check=True,
  ).stdout.split()
  return sorted(os.path.basename(p)[:-5] for p in out if p.endswith('.json'))

def parse_selection(args: list[str], root: str = '.') -> list[str]:
  if '--ids' in args:
    return json.load(open(args[args.index('--ids')+1], encoding='utf-8'))
  if '--since' in args:
    return changed_since(args[args.index('--since')+1], root)
  raise SystemExit('pass --ids <file.json> or --since <git-ref>')
