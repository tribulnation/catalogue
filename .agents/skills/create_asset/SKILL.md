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

2. Create asset translations and instruments for MEXC spot and dYdX.

  Create entries in:
   - `data/asset_translations/mexc.json` and `data/asset_translations/dydx.json`
   - `data/instruments/spot/mexc.json` and `data/instruments/perpetual/dydx.json`

  You can research these:
  - For MEXC: check `https://api.mexc.com/api/v3/avgPrice?symbol=<instrument_id>`. Make sure it returns a valid price and that it matches what you found in coingecko.
  - For dYdX: check `https://indexer.dydx.trade/v4/perpetualMarkets?market=<instrument_id>`. Make sure it returns a valid price and that it matches what you found in coingecko.

3. Try to create asset SVG icon. I'd recommend searching online for "bit2me <asset_name>". Most assets have a page `https://bit2me.com/es/precio/<asset_id>`. Inside, they'll have a like to an SVG icon. Donwload it and standardize it:
  - Square background: no circles or similar
  - Remove `<?xml version="1.0" encoding="UTF-8"?>` at the top of the file
  - Remove unnecessary tags (e.g. `id="..."`) and rename used IDs to be shorter (e.g. `degradado1` to `g1`)