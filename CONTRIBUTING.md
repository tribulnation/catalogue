# Contributing

Contributions are welcome — new assets, platforms, icons, translations, instrument mappings, and corrections all help.

## Setup

```bash
git clone https://github.com/tribulnation/catalogue2.git
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

## Releasing the Python package

`tribulnation-catalogue` publishes to PyPI from CI, triggered by merging a pull request
from the `release/python` branch. Nothing is published from a developer machine.

1. Bump `version` in `lib/pyproject.toml`. This is deliberately manual — a version bump
   is a decision, not a side effect of merging.
2. Open a pull request from `release/python` into `main`. Its body becomes the GitHub
   Release notes, so write it as a changelog.
3. Merge it. `.github/workflows/release-python.yml` then checks whether that version is
   already on PyPI, and if not runs `pyright`, builds, publishes, tags `python-v<version>`,
   and drafts the GitHub Release.

The branch name is the gate: an ordinary pull request touching `lib/` publishes nothing.
Re-merging an already-published version is a no-op, so a re-run is safe.

To check the release gate locally before opening the pull request:

```bash
.venv/bin/pyright lib && .venv/bin/python -m build lib
```

The npm package under `js/` is still released manually via `js/Justfile`.
