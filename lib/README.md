# tribulnation-catalogue

[![PyPI](https://img.shields.io/pypi/v/tribulnation-catalogue)](https://pypi.org/project/tribulnation-catalogue/)
[![Python](https://img.shields.io/pypi/pyversions/tribulnation-catalogue)](https://pypi.org/project/tribulnation-catalogue/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/tribulnation/catalogue/blob/main/LICENSE)

Python client for the [Tribulnation Catalogue](https://github.com/tribulnation/catalogue) — a typed, open catalogue of crypto assets, trading platforms, and instrument mappings.

## Install

```bash
pip install tribulnation-catalogue
```

## Usage

```python
from tribulnation.catalogue import Catalogue

catalogue = Catalogue.load()

btc     = catalogue.assets["bitcoin"]
binance = catalogue.platforms["binance"]
```

On first call, `load()` downloads the catalogue and caches it at `~/.cache/tribulnation/catalogue`. Subsequent calls load from cache.

## Loading options

```python
# Use cache, download if not present (default)
catalogue = Catalogue.load()

# Force a fresh download
catalogue = Catalogue.load(refresh=True)

# Load from an explicit local folder
catalogue = Catalogue.load("data")

# Custom source URL or cache directory
catalogue = Catalogue.load(
    url="https://my-mirror.example.com/data.zip",
    cache_dir=".cache/catalogue",
)

# Suppress the download message
catalogue = Catalogue.load(silent=True)
```

## What's available

```python
catalogue.assets           # dict[str, Asset]
catalogue.platforms        # dict[str, Platform]
catalogue.blockchains      # filtered view: kind == 'blockchain'
catalogue.cexs             # filtered view: kind == 'cex'
catalogue.dexs             # filtered view: kind == 'dex'

catalogue.spot_instruments        # dict[platform, dict[id, Spot]]
catalogue.perpetual_instruments   # dict[platform, dict[id, Perpetual]]
catalogue.debt_instruments        # dict[platform, dict[id, Debt]]
catalogue.pools                   # dict[platform, dict[id, Pool]]

catalogue.asset_translations      # dict[platform, dict[exchange_id, asset_id]]
catalogue.network_translations    # dict[platform, dict[exchange_id, network_id]]

catalogue.spam                    # dict[platform, dict[address, SpamAddress]]
```

## Types

All types are available from the package root:

```python
from tribulnation.catalogue import (
    Asset, AssetPeg, ExternalIds,
    Platform, Blockchain, CexPlatform, DexPlatform,
    Spot, Perpetual, Debt, Pool,
    SpamAddress,
)
```

## Links

- [Full catalogue & API](https://catalogue.tribulnation.com)
- [GitHub](https://github.com/tribulnation/catalogue)
- [JavaScript package](https://www.npmjs.com/package/@tribulnation/catalogue)
