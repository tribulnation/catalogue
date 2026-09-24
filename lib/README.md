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

`load()` keeps the published `data.zip` in `~/.cache/tribulnation` and loads it from there. Once a day (`max_age`) it asks the site whether the archive changed with one conditional request (`ETag` / `Last-Modified`), and downloads it again only when it did. A download replaces the cached copy only once it loads; if the site is unreachable, the last good copy is used and a warning is logged. Only a first run without any cached copy fails.

## Loading options

```python
# Cached archive, checked at most once a day (default)
catalogue = Catalogue.load()

# Check more or less often
catalogue = Catalogue.load(max_age=timedelta(hours=6))

# Force a fresh download
catalogue = Catalogue.load(refresh=True)

# Load from an explicit local folder (never touches the network once it exists)
catalogue = Catalogue.load("data")

# Custom source URL or cache directory
catalogue = Catalogue.load(
    url="https://my-mirror.example.com/data.zip",
    cache_dir=".cache/catalogue",
)

# Suppress the download message
catalogue = Catalogue.load(silent=True)
```

### Long-running processes

```python
catalogue = Catalogue.load()
catalogue.digest     # sha256 of the loaded data.zip (None for a folder)
catalogue.loaded_at  # when it was loaded

# Call as often as you like (e.g. daily): returns the same object until max_age
# elapsed and the published archive actually changed, then a freshly loaded one.
catalogue = catalogue.maybe_refresh()

# Check now, regardless of max_age
catalogue = catalogue.refresh()
```

Network errors never raise from `maybe_refresh()` / `refresh()`; the last good copy stays.

## Lookups

```python
catalogue.asset_for('hyperliquid', 150)        # 'hyperliquid'  (spot token index)
catalogue.asset_for('arbitrum', '0xaf88d065e77c8cc2239327c5edb3a432268e5831')  # 'usd-coin' (any casing)
catalogue.asset_for('ethereum', 'native')      # 'ethereum'
catalogue.asset_for('bitget', 'rSPY')          # symbols are case-sensitive
catalogue.asset_for('mexc', 'UNKNOWN')         # None

catalogue.perpetual_for('hyperliquid', 'kPEPE')
# PerpetualInstrument(platform='hyperliquid', id='kPEPE', base='pepe', quote='tether',
#                     settlement='usd-coin', multiplier=Decimal('1000'), delisted=False)

catalogue.network_for('bybit', 'BSC (BEP20)')  # 'bnb-chain'
catalogue.canonical_id('old-id')               # follows `replaced_by` aliases
```

Every lookup follows `replaced_by`: asset ids are never deleted, and a merged asset keeps its file as an alias of the surviving one.

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
    Spot, Perpetual, PerpetualInstrument, Debt, Pool,
    SpamAddress,
)
```

## Links

- [Full catalogue & API](https://catalogue.tribulnation.com)
- [GitHub](https://github.com/tribulnation/catalogue)
- [JavaScript package](https://www.npmjs.com/package/@tribulnation/catalogue)
