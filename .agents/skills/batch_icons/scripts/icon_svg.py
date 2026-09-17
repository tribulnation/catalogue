"""Shared SVG helpers for the batch_icons skill.

Pure stdlib except `measure`/`fit`, which need `cairosvg` and `pillow`.
"""
import io as _io
import math as _math
import re as _re

def strip_prolog(svg: str) -> str:
  return _re.sub(r'<\?xml[^>]*\?>', '', svg).strip()

def flatten_styles(svg: str) -> str:
  """Inline a <style> block's class rules as presentation attributes.

  Icons that carry `<style>` + `class="st0"` cannot be embedded into another
  SVG or into a page next to other icons: the class names are global, so the
  last definition wins and glyphs get repainted. Inlining makes them portable.
  """
  rules: dict[str, str] = {}
  for block in _re.finditer(r'<style[^>]*>(.*?)</style>', svg, _re.S):
    for sel, decls in _re.findall(r'\.([A-Za-z0-9_-]+)\s*\{([^}]*)\}', block.group(1)):
      rules[sel] = decls.strip().rstrip(';')
  svg = _re.sub(r'<style[^>]*>.*?</style>', '', svg, flags=_re.S)
  def attrs(m: _re.Match) -> str:
    out = []
    for name in m.group(1).split():
      for decl in rules.get(name, '').split(';'):
        if ':' in decl:
          k, v = decl.split(':', 1)
          out.append(f'{k.strip()}="{v.strip()}"')
    return ' '.join(out)
  return _re.sub(r'class="([^"]+)"', attrs, svg)

def namespace_ids(svg: str, prefix: str) -> str:
  """Prefix every id and its references, so many icons can share one document."""
  for id in sorted(set(_re.findall(r'\sid="([^"]+)"', svg)), key=len, reverse=True):
    new = f'{prefix}-{id}'
    svg = svg.replace(f'id="{id}"', f'id="{new}"')
    svg = svg.replace(f'url(#{id})', f'url(#{new})')
    svg = svg.replace(f'href="#{id}"', f'href="#{new}"')
  return svg

def split_root(svg: str) -> tuple[str, str, str]:
  """Return (viewBox, inner markup, presentation attributes of the root <svg>).

  The root's own `fill`/`stroke`/`fill-rule` matter: an icon whose root carries
  `fill="none"` loses its glyph when the inner markup is re-parented without it.
  """
  m = _re.search(r'<svg\b([^>]*)>(.*)</svg\s*>\s*$', strip_prolog(svg), _re.S)
  if m is None:
    raise ValueError('not an svg document')
  attrs, body = m.group(1), m.group(2)
  vb_match = _re.search(r'viewBox="([^"]+)"', attrs)
  if vb_match is None:
    raise ValueError('svg has no viewBox')
  extra = ''
  for name in ('fill', 'stroke', 'fill-rule', 'xmlns:xlink'):
    found = _re.search(r'\s%s="([^"]*)"' % _re.escape(name), attrs)
    if found:
      extra += f' {name}="{found.group(1)}"'
  return vb_match.group(1), body.strip('\n'), extra

def background(svg: str) -> tuple[str | None, str | None]:
  """The square background rect and its colour, if the icon has one."""
  m = _re.search(r'<rect[^>]*/>', svg)
  if m is None:
    return None, None
  colour = _re.search(r'fill="([^"]+)"', m.group(0))
  return m.group(0), colour.group(1) if colour else None

def measure(svg: str, size: int = 512):
  """Alpha bounding box of the rendered markup, in canvas pixels."""
  import cairosvg
  from PIL import Image
  png = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
  image = Image.open(_io.BytesIO(png)).convert('RGBA')
  return image.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox()

def fit(path: str, target: float = 0.80, mode: str = 'box', size: int = 512):
  """Re-centre and re-scale an icon's glyph inside the maskable safe zone.

  `mode='box'` sizes the glyph's longest side to `target` of the canvas — the
  house default. `mode='radius'` sizes its diagonal instead, for glyphs whose
  corners would otherwise poke out of the inscribed circle.
  """
  svg = open(path, encoding='utf-8').read()
  x0, y0, w, h = [float(v) for v in _re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
  bg_tag, bg_colour = background(svg)
  body = svg.replace(bg_tag, '', 1) if bg_tag else svg
  probe = body
  if bg_colour:
    # shapes painted in the background colour are invisible: ignore them
    probe = _re.sub(r'<(circle|rect|path|polygon)[^>]*fill="%s"[^>]*/>' % _re.escape(bg_colour), '', probe, flags=_re.I)
  box = measure(probe, size)
  if box is None:
    raise ValueError(f'{path}: nothing visible to measure')
  scale_to_user = w / size
  gx0, gy0, gx1, gy1 = [v*scale_to_user for v in box]
  gw, gh = gx1-gx0, gy1-gy0
  span = _math.hypot(gw, gh) if mode == 'radius' else max(gw, gh)
  factor = (target*w) / span
  tx = (x0+w/2) - factor*(gx0+gw/2)
  ty = (y0+h/2) - factor*(gy0+gh/2)
  head = svg.split('>', 1)[0] + '>'
  inner = body.split('>', 1)[1].rsplit('</svg', 1)[0].strip()
  out = (
    head + '\n'
    + (f'  {bg_tag}\n' if bg_tag else '')
    + f'  <g transform="translate({tx:.2f},{ty:.2f}) scale({factor:.4f})">\n'
    + '\n'.join('  ' + line for line in inner.split('\n') if line.strip()) + '\n'
    + '  </g>\n</svg>\n'
  )
  open(path, 'w', encoding='utf-8').write(out)
  return factor
