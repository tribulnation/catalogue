"""Build a self-contained review page for a batch of icons.

Each asset gets a card: the icon rendered square and clipped to the inscribed
circle, its name/symbol/id, where the artwork came from, a "not accepted"
toggle and a notes box. A Copy results button hands back a markdown list of
what was rejected, which is what the next round works from.

    python3 .agents/skills/batch_icons/scripts/build_review.py \
      --since origin/main --sources reports/ --round r1 --out review.html

Publish the result with the Artifact tool. `--round` names the review round:
bumping it clears the stored marks of assets whose entry carries a `revised`
note, so a reviewer re-judges only what changed.
"""
import glob
import json
import os
import sys

import icon_svg
from derive_icons import icon_of, load
from select_ids import parse_selection

def read_sources(folder: str | None) -> dict:
  """Merge the sourcing agents' JSON reports: [{id, status, source, note}, ...]."""
  rows: dict[str, dict] = {}
  if not folder:
    return rows
  for path in sorted(glob.glob(os.path.join(folder, '*.json'))):
    for row in json.load(open(path, encoding='utf-8')):
      rows[row['id']] = row
  return rows

def classify(id: str, icon: str | None, svg: str | None) -> tuple[str, str | None]:
  if icon is None or svg is None:
    return 'missing', None
  if os.path.basename(icon)[:-4] != id:
    return 'shared', f'reuses {icon} (no separate artwork exists)'
  if 'B6509E' in svg and 'linearGradient' in svg:
    return 'aave-frame', None
  return 'sourced', None

def entries(ids: list[str], sources: dict, revised: dict, root: str = '.') -> list[dict]:
  out = []
  for n, id in enumerate(ids):
    asset = load(id, root)
    if asset is None:
      continue
    icon = icon_of(id, root)
    svg = None
    if icon:
      raw = icon_svg.flatten_styles(icon_svg.strip_prolog(open(os.path.join(root, icon), encoding='utf-8').read()))
      svg = icon_svg.namespace_ids(raw, f'a{n}')     # ids are global in one page
    method, note = classify(id, icon, svg)
    report = sources.get(id, {})
    out.append({
      'id': id, 'name': asset.get('display_name'), 'symbol': asset.get('symbol'),
      'icon': icon, 'svg': svg, 'method': method,
      'source': report.get('source'), 'note': report.get('note') or note,
      'revised': revised.get(id),
    })
  return out

def build(ids: list[str], out: str, sources: dict, revised: dict, round: str, root: str = '.'):
  data = entries(ids, sources, revised, root)
  template = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'review_page.html'), encoding='utf-8').read()
  counts = {}
  for entry in data:
    counts[entry['method']] = counts.get(entry['method'], 0) + 1
  subtitle = (
    f'{len(data)} assets in this batch &mdash; square render and inscribed-circle mask, side by side. '
    + ', '.join(f'{v} {k}' for k, v in sorted(counts.items())) + '.'
  )
  page = (template
    .replace('__SUBTITLE__', subtitle)
    .replace('__ROUND__', round)
    .replace('__DATA__', json.dumps(data).replace('</', '<\\/')))   # keep </script> out of the blob
  open(out, 'w', encoding='utf-8').write(page)
  return data

if __name__ == '__main__':
  args = sys.argv[1:]
  def opt(flag, fallback=None):
    return args[args.index(flag)+1] if flag in args else fallback
  revised = json.load(open(opt('--revised'), encoding='utf-8')) if '--revised' in args else {}
  data = build(
    parse_selection(args), opt('--out', 'review.html'),
    read_sources(opt('--sources')), revised, opt('--round', 'r1'),
  )
  print(f"{opt('--out', 'review.html')}: {len(data)} cards")
