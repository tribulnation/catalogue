# Catalogue SVG Icons Guidelines

## Content

- The icon must be square: use a square `viewBox`/canvas and a square background.
- The background should be the main color of the asset/platform. The details/accent should be white/black (depending on contrast) or secondary asset/platform color.
- The icon main glyph must be centered, vertically and horizontally.
- The glyph should have enough padding to avoid being cropped when displayed in a circle. I.e. the icon must be maskable.
- Avoid layered shapes that repaint the background color over foreground details to simulate cutouts. These often create clipped or fuzzy edges where anti-aliased shapes overlap. Prefer an existing SVG where the visible foreground glyph is drawn directly, or one that uses a proper mask/clip path for real cutouts.

## SVG Format

- Use an XML formatter to automatically format the content
- Remove `<?xml version="1.0" encoding="UTF-8"?>` at the top of the file
- Remove unnecessary tags (e.g. `id="..."`) and rename used IDs to be shorter (e.g. `degradado1` to `g1`)

## Others

- Don't set a `width` or `height` on the `<svg>` tag, let the `viewBox` define the size.
- Avoid nested `<svg>` tags, use `<g>` with `transform` instead.
- Don't embed a PNG inside the SVG: use only vector shapes and text.
- Never generate the SVGs manually. Find an existing one online or skip it altogether.

## Recommended Sources

Places where you can find SVG icons:

- Bit2me: https://bit2me.com/es/precio/<asset_id_or_symbol_or_name>
- TradingView: https://www.tradingview.com/symbols/<pair>/. The page usually loads SVG icons from an s3 bucket, e.g. `https://s3-symbol-logo.tradingview.com/crypto/XTVCBNB--big.svg`
- Find a PNG/WEBP etc. image instead from preferrably official sources and convert it to SVG using a vectorization tool. Then inspect the original image and make sure the SVG is properly colored. Make sure to adapt the content to the requirements above (square, centered, maskable, etc.).