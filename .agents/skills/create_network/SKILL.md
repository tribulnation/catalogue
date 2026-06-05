---
name: Create Network
description: Create all catalogue data for a blockchain network/platform, including data/platforms entries, platform order, icons, native asset linkage, and optional exchange network translations.
---

Use this when adding a blockchain network/platform. This is different from adding a tradable asset.

1. Inspect the schema and nearby examples before editing:
   - Schema: `lib/src/tribulnation/catalogue/schema.py`
   - Platform examples: `data/platforms/ethereum.json`, `data/platforms/solana.json`, `data/platforms/base.json`, and any similar network.
   - Platform order: `data/platforms/order.txt`
   - Network translations: `data/network_translations/*.json`

2. Create `data/platforms/<id>.json`.
   - Use `kind: "blockchain"`.
   - Set `display_name`.
   - Set `native_asset` when the network has a known native asset already present in `data/assets/`. If the native asset is missing, create the asset first or stop and explain the dependency.
   - Add `about` in English, Spanish, and Catalan.
   - Add `urls.Website`.
   - Add `icon` when a suitable icon exists. Most blockchain platforms reuse `icons/asset/<native_asset>.svg`; use `icons/network/<id>.svg` only when the repo already uses or needs a separate network icon.

3. Add `<id>` to `data/platforms/order.txt`.
   - Place it near comparable networks, preserving the existing rough priority/grouping.

4. Research exchange network IDs only when relevant.
   - Update `data/network_translations/mexc.json`, `binance.json`, `bitget.json`, or `kraken.json` only when you can verify the platform-specific network name from the exchange/API or reliable docs.
   - Do not guess exchange network IDs from ticker symbols.

5. Validate with the repo virtualenv:
   - `.venv/bin/python validate.py`

6. In the final response, mention:
   - The platform file created.
   - Whether `native_asset` and `icon` were set.
   - Any network translations added or intentionally skipped.
   - Validation result.
