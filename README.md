# Tribulnation Catalogue

[![Validate](https://github.com/tribulnation/catalogue/actions/workflows/validate.yml/badge.svg)](https://github.com/tribulnation/catalogue/actions/workflows/validate.yml)
[![Deploy](https://github.com/tribulnation/catalogue/actions/workflows/deploy.yml/badge.svg)](https://github.com/tribulnation/catalogue/actions/workflows/deploy.yml)
[![PyPI](https://img.shields.io/pypi/v/tribulnation-catalogue)](https://pypi.org/project/tribulnation-catalogue/)
[![npm](https://img.shields.io/npm/v/@tribulnation/catalogue)](https://www.npmjs.com/package/@tribulnation/catalogue)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A typed, open catalogue of crypto assets, trading platforms, instrument mappings, and name translations — built to resolve the inconsistent IDs and symbols that exchanges, wallets, chains, and market data APIs throw at you.

![Stats](https://catalogue.tribulnation.com/stats.svg)

---

## API

Every record in this catalogue is available as a static JSON API — no auth, no rate limits, served from GitHub Pages.

**Browse: [catalogue.tribulnation.com](https://catalogue.tribulnation.com)**

```
GET /api/stats.json
GET /api/assets.json
GET /api/assets/{id}.json
GET /api/platforms.json
GET /api/platforms/{id}.json
GET /api/instruments/spot/{platform}.json
GET /api/instruments/perpetual/{platform}.json
GET /api/instruments/index/{asset}.json
GET /api/indexes/symbols.json
GET /api/indexes/external/coingecko.json
GET /api/openapi.json
```

Full route list and interactive 'try it' at [catalogue.tribulnation.com/api](https://catalogue.tribulnation.com/api).

Download everything at once:

| Archive | Contents |
|---|---|
| [`data.zip`](https://catalogue.tribulnation.com/data.zip) | Raw catalogue data (JSON) |
| [`icons.zip`](https://catalogue.tribulnation.com/icons.zip) | SVG icons for assets, platforms, networks |

---

## Clients

### JavaScript / TypeScript

```bash
npm install @tribulnation/catalogue
```

```tsx
import { Catalogue } from '@tribulnation/catalogue';

const client = new Catalogue();
const matches = await client.findBySymbol('BTC');

return (
  matches.map((match) => (
    <div>
      <p>{match.display_name}</p>
      <img src={match.icon} alt={`Image of ${match.id}`} />
    </div>
  ))
)

// Fetch individual records
const bitcoin = await client.fetchAsset('bitcoin');
const pairs   = await client.getSpotInstruments('mexc');
```

### Python

```bash
pip install tribulnation-catalogue
```

```python
from tribulnation.catalogue import Catalogue

catalogue = Catalogue.load()

btc     = catalogue.assets['bitcoin']
binance = catalogue.platforms['binance']
```

`Catalogue.load()` downloads the public catalogue on first use and caches it locally for later runs.

```python
catalogue = Catalogue.load()             # use cache, download if needed
catalogue = Catalogue.load(refresh=True) # force fresh download
catalogue = Catalogue.load('data')       # explicit local folder
```

---

## What's inside

### Assets
Canonical records keyed by slug (e.g. `bitcoin`, `usd-coin`). Each asset has a `display_name`, `symbol`, optional `icon`, `tags`, peg information for stablecoins and wrapped tokens, and external IDs mapping to third-party providers:

| Field | Provider |
|---|---|
| `coingecko` | CoinGecko asset ID |
| `coinmarketcap` | CoinMarketCap asset ID |
| `twelvedata` | Twelve Data symbol (e.g. `XAU/USD`) |
| `alphavantage` | Alpha Vantage function or forex pair (e.g. `WTI`, `EUR/USD`) |

### Platforms
Trading venues and networks keyed by slug (e.g. `binance`, `ethereum`). Covers CEX, DEX, and blockchain platforms. Blockchains carry `namespace`, `chain_id`, `native_asset`, and EVM/SVM `category`.

### Instruments
Spot pairs, perpetual futures, debt positions, collateral positions, and liquidity pools — each referencing canonical asset IDs. Maps exchange-specific tickers to the catalogue's canonical identifiers.

### Translations
Per-platform display-name mappings for assets and networks. Resolves what a given exchange calls `BTC/USDT` into `('bitcoin', 'tether')`.

### Icons
SVG icons for assets, platforms, and networks, organized under `icons/asset/`, `icons/platform/`, and `icons/network/`. All icons are **square and maskable** — they include a full square background and are designed to be displayed cropped to a circle or rounded square. API responses include absolute icon URLs.

### Spam
Known spam token addresses per chain, with optional source and reported timestamp.

---

## Contributing

Contributions are welcome — new assets, platforms, icons, translations, and corrections.

```bash
git clone https://github.com/tribulnation/catalogue.git
cd catalogue
python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Add or edit files under `data/` and `icons/`, then validate:

```bash
.venv/bin/python scripts/validate.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full data layout and field reference.
