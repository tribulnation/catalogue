"""Re-centre and re-scale an icon's glyph inside the maskable safe zone.

    python3 .agents/skills/batch_icons/scripts/fit_icon.py icons/asset/<id>.svg
    python3 .agents/skills/batch_icons/scripts/fit_icon.py --radius icons/asset/<id>.svg

Default mode sizes the glyph's longest side to 80% of the canvas. `--radius`
sizes its diagonal to 78% instead — use it when a glyph measures 80% wide but
its corners still poke through the inscribed circle.

Needs `cairosvg` and `pillow`.
"""
import sys

import icon_svg

if __name__ == '__main__':
  args = sys.argv[1:]
  mode = 'radius' if '--radius' in args else 'box'
  target = 0.78 if mode == 'radius' else 0.80
  for path in [a for a in args if not a.startswith('--')]:
    factor = icon_svg.fit(path, target=target, mode=mode)
    print(f'{path}: scaled {factor:.3f}, centred ({mode})')
