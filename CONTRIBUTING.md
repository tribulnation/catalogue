# Contributing

Contributions are welcome — new assets, platforms, icons, translations, instrument mappings, and corrections all help.

## Setup

```bash
git clone https://github.com/tribulnation/catalogue.git
cd catalogue
python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

## Data layout

```
data/
  assets/             one JSON file per asset (e.g. bitcoin.json)
  platforms/          one JSON file per platform (e.g. binance.json)
  instruments/
    spot/             spot pairs per platform
    perpetual/        perpetual futures per platform
    debt/             debt positions per platform
    pools/            liquidity pools per platform
  asset_translations/ per-platform display name overrides for assets
  network_translations/ per-platform display name overrides for networks
  spam/               known spam token addresses per chain

icons/
  asset/              SVG icons for assets (e.g. bitcoin.svg)
  platform/           SVG icons for platforms
  network/            SVG icons for networks
```

## Adding an asset

Create `data/assets/<slug>.json`. Required fields:

```json
{
  "display_name": "My Token",
  "symbol": "MTK",
  "tags": ["defi"]
}
```

Optional fields: `about` (locale → string), `urls` (name → url), `pegged_to` (`{"asset": "<slug>"}`), `external` (`{"coingecko": "<id>"}`), `icon` (path relative to `icons/`).

## Adding a platform

Create `data/platforms/<slug>.json`. Required fields:

```json
{
  "display_name": "My Exchange",
  "kind": "cex"
}
```

`kind` is one of `cex`, `dex`, or `blockchain`. Blockchains also accept `native_asset`, `namespace`, `chain_id`, and `category`.

## Validate

Always run before opening a pull request:

```bash
.venv/bin/python scripts/validate.py
```

The CI will run this automatically on every push and pull request.
