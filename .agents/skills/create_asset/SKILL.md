---
name: Create Asset
description: Create all data for a new asset.
---

Follow `.agents/rules/pull_requests.md` for sourcing, validation, PR description, and branching conventions. Follow `.agents/rules/icons.md` for all icon requirements.

1. Create a new `data/assets/<id>.json`. Research online for:
  - Display name
  - Symbol
  - About (description) in English, Spanish, and Catalan
  - Coingecko ID
  - Keep the URL of every source used (official site, CoinGecko page, etc.) for the PR description.

2. Try to download the asset SVG icon. I'd recommend searching online for "bit2me <asset_name>". Most assets have a page `https://bit2me.com/es/precio/<asset_id>`. Inside, they'll have a link to an SVG icon. Download it and standardize it per `.agents/rules/icons.md`:
  - Square canvas and square background, main glyph centered, padded to clear the inscribed-circle mask.
  - Remove `<?xml version="1.0" encoding="UTF-8"?>` at the top of the file.
  - Remove unnecessary tags (e.g. `id="..."`) and rename used IDs to be shorter (e.g. `degradado1` to `g1`).
  - If you don't find a suitable SVG, ignore it and say that you couldn't find one.

3. Validate with the repo virtualenv:
   - `PYTHONPATH=lib/src .venv/bin/python scripts/validate.py`

4. Open the PR per `.agents/rules/pull_requests.md` (summary, sources, icon preview + circle-crop check if an icon was added, test plan), then subscribe to its activity.
