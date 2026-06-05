---
name: Create Asset
description: Create all data for a new asset.
---

1. Create a new `data/assets/<id>.json`. Research online for:
  - Display name
  - Symbol
  - Display decimals (depending on the current price. Essentially, it should be such that the value of 1 unit rounds to 2 decimals)
  - About (description) in English, Spanish, and Catalan
  - Coingecko ID

2. Try to create asset SVG icon. I'd recommend searching online for "bit2me <asset_name>". Most assets have a page `https://bit2me.com/es/precio/<asset_id>`. Inside, they'll have a like to an SVG icon. Donwload it and standardize it:
  - The icon must be square: use a square `viewBox`/canvas and a square background.
  - Square background: no circles or similar
  - Remove `<?xml version="1.0" encoding="UTF-8"?>` at the top of the file
  - Remove unnecessary tags (e.g. `id="..."`) and rename used IDs to be shorter (e.g. `degradado1` to `g1`)
