"""Render a contact sheet of icons, square and clipped to the inscribed circle.

The circle sheet is the maskability check from `.agents/rules/icons.md`, and
both belong in the PR description (see `.agents/rules/pull_requests.md`).

    python3 .agents/skills/batch_icons/scripts/contact_sheet.py --ids ids.json --out sheet
    python3 .agents/skills/batch_icons/scripts/contact_sheet.py --since origin/main --out sheet

Writes `<out>-square.png` and `<out>-circle.png`. Needs `cairosvg` and `pillow`.
"""
import io
import json
import os
import sys

import cairosvg
from PIL import Image, ImageDraw

from select_ids import parse_selection
from derive_icons import icon_of

CELL, PAD, COLUMNS, LABEL = 88, 12, 12, 14

def render(icon: str, size: int, circle: bool) -> Image.Image:
  png = cairosvg.svg2png(url=icon, output_width=size, output_height=size)
  tile = Image.open(io.BytesIO(png)).convert('RGBA')
  if circle:
    mask = Image.new('L', (size*4, size*4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size*4-1, size*4-1), fill=255)
    tile.putalpha(mask.resize((size, size), Image.LANCZOS))
  return tile

def sheet(ids: list[str], circle: bool, root: str = '.') -> Image.Image:
  rows = (len(ids) + COLUMNS - 1) // COLUMNS
  step = CELL + PAD + LABEL
  canvas = Image.new('RGBA', (COLUMNS*(CELL+PAD) + PAD, rows*step + PAD), (242, 243, 245, 255))
  draw = ImageDraw.Draw(canvas)
  for n, id in enumerate(ids):
    icon = icon_of(id, root)
    if icon is None:
      continue
    x = PAD + (n % COLUMNS)*(CELL+PAD)
    y = PAD + (n // COLUMNS)*step
    canvas.alpha_composite(render(os.path.join(root, icon), CELL, circle), (x, y))
    draw.text((x, y+CELL+3), id[:18], fill=(60, 66, 74))
    if len(id) > 18:
      draw.text((x, y+CELL+12), id[18:36], fill=(60, 66, 74))
  return canvas

if __name__ == '__main__':
  args = sys.argv[1:]
  out = args[args.index('--out')+1] if '--out' in args else 'sheet'
  ids = parse_selection(args)
  for circle in (False, True):
    path = f'{out}-{"circle" if circle else "square"}.png'
    sheet(ids, circle).save(path)
    print(f'{path}: {len(ids)} icons')
