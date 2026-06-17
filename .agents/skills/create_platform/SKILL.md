---
name: Create Platform
description: Create all catalogue data for a non-blockchain trading platform, such as a centralized exchange or decentralized exchange.
---

Use this when adding a trading platform or venue. This is different from adding a tradable asset, and different from adding a blockchain network.

1. Inspect the schema and nearby examples before editing:
   - Schema: `lib/src/tribulnation/catalogue/schema.py`
   - CEX examples: `data/platforms/binance.json`, `data/platforms/bybit.json`, `data/platforms/kraken.json`, and any similar platform.
   - DEX examples: `data/platforms/dydx.json`, `data/platforms/hyperliquid.json`, and any similar platform.
   - Platform order: `data/platforms/order.txt`
   - Asset translations: `data/asset_translations/*.json`
   - Instrument data, if relevant: `data/spot_instruments/` and `data/perpetual_instruments/`

2. Research the platform from primary or reliable sources.
   - Confirm the platform's official display name.
   - Confirm whether it is a centralized exchange (`kind: "cex"`) or decentralized exchange (`kind: "dex"`).
   - Confirm its official website URL.
   - Look for a short factual description: market type, main products, launch/founding context when notable, geography/regulatory scope when relevant, and distinguishing features.
   - Do not add unsupported claims. If a claim is uncertain, leave it out.

3. Create `data/platforms/<id>.json`.
   - Set `display_name`.
   - Set `kind` to either `"cex"` or `"dex"`.
   - Add `about` in English, Spanish, and Catalan.
   - Add `urls.Website`.
   - Add `urls.Referral` only when a verified referral URL is already known or explicitly provided.
   - Add `icon` when a suitable SVG exists.
   - Do not set `native_asset`; that field is only for `kind: "blockchain"`.

4. Add or create the platform icon.
   - Prefer an official SVG from the platform website, app assets, press kit, brand kit, or official repository.
   - Use an existing repo icon only when it clearly represents the same platform or brand.
   - Do not use JPG, PNG, WebP, favicon ICO, or raster images as the source.
   - If no suitable SVG exists, skip the icon and say so.
   - Icons must be square: use a square `viewBox`/canvas and a square background, even when centering a wide wordmark inside it.
   - Remove `<?xml version="1.0" encoding="UTF-8"?>` at the top of the file.
   - Remove unnecessary tags and metadata. Rename used IDs to short stable names when needed.

5. Add `<id>` to `data/platforms/order.txt`.
   - Place CEX platforms near comparable CEX entries, preserving the existing rough priority/grouping.
   - Place DEX platforms near comparable DEX entries, preserving the existing rough priority/grouping.

6. Add translations or instruments only when requested or clearly in scope.
   - Asset translations map platform-specific symbols/IDs to catalogue asset IDs in `data/asset_translations/<platform>.json`.
   - Spot and perpetual instruments belong in their corresponding platform files only when the task asks for market/instrument coverage.
   - Do not guess platform-specific IDs. Verify them from the platform UI, API, docs, or reliable exchange listings.

7. Validate with the repo virtualenv:
   - `.venv/bin/python validate.py`

8. In the final response, mention:
   - The platform file created.
   - Whether the platform is `cex` or `dex`.
   - Whether an icon was added or skipped, and why.
   - Any translations or instruments added or intentionally skipped.
   - Validation result.
