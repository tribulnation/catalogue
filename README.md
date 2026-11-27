# Tribulnation Catalogue

[![Validate](https://github.com/tribulnation/catalogue/actions/workflows/validate.yml/badge.svg)](https://github.com/tribulnation/catalogue/actions/workflows/validate.yml)
[![Deploy](https://github.com/tribulnation/catalogue/actions/workflows/deploy.yml/badge.svg)](https://github.com/tribulnation/catalogue/actions/workflows/deploy.yml)
[![PyPI](https://img.shields.io/pypi/v/tribulnation-catalogue)](https://pypi.org/project/tribulnation-catalogue/)
[![npm](https://img.shields.io/npm/v/@tribulnation/catalogue)](https://www.npmjs.com/package/@tribulnation/catalogue)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

An open catalogue of crypto assets, networks and instruments, with the names each exchange and chain uses for them.

Every exchange names things its own way. Binance calls BNB Chain `BSC`, MEXC calls it `BNB Smart Chain(BEP20)` and Bybit `BSC (BEP20)`. Kraken calls bitcoin `XXBT` and Hyperliquid calls it `197`. The catalogue maps all of these to one id (`bnb-chain`, `bitcoin`), so code that talks to several venues can agree on what it holds.

![Stats](https://catalogue.tribulnation.com/stats.svg)

## Why use it

- The data is JSON files in this repo, MIT licensed. A wrong mapping is fixed with a pull request.
- The JSON API needs no key, and `data.zip` and `icons.zip` hold everything for offline use.
- Typed clients for Python and TypeScript look up assets, networks, and spot, margin and perpetual markets.
- Asset ids are never deleted. A merged asset stays as an alias (`replaced_by`) of the one that replaced it.
- Assets, platforms and networks come with square SVG icons that crop cleanly to a circle.

## Quickstart

Ask the API what Kraken means by `XXBT`:

```bash
curl https://catalogue.tribulnation.com/api/v1/translate/kraken/XXBT.json
```

```json
{
  "id": "bitcoin",
  "kind": "asset"
}
```

Or do the same lookups in Python:

```bash
pip install tribulnation-catalogue
```

```python
from tribulnation.catalogue import Catalogue

catalogue = Catalogue.load()

print(catalogue.asset_for('kraken', 'XXBT'))
print(catalogue.network_for('bybit', 'BSC (BEP20)'))
print(catalogue.perpetual_for('hyperliquid', 'kPEPE'))
```

```
bitcoin
bnb-chain
PerpetualInstrument(platform='hyperliquid', id='kPEPE', base='pepe', quote='tether', settlement='usd-coin', multiplier=Decimal('1000'), delisted=False, quanto=None)
```

---

## API

Every record is available as a static JSON API, served from Cloudflare. No API key is needed.

**Browse: [catalogue.tribulnation.com](https://catalogue.tribulnation.com)**

```
GET /api/v1/stats.json
GET /api/v1/assets.json
GET /api/v1/assets/{id}.json
GET /api/v1/platforms.json
GET /api/v1/platforms/{id}.json
GET /api/v1/instruments/spot/{platform}.json
GET /api/v1/instruments/margin/{platform}.json
GET /api/v1/instruments/perpetual/{platform}.json
GET /api/v1/instruments/index/{asset}.json
GET /api/v1/translate/{platform}/{id}.json
GET /api/v1/indexes/symbols.json
GET /api/v1/indexes/external/coingecko.json
GET /api/v1/openapi.json
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

```js
import { Catalogue } from '@tribulnation/catalogue';

const catalogue = new Catalogue();

console.log(await catalogue.translate('kraken', 'XXBT'));

const [btc] = await catalogue.findBySymbol('BTC');
console.log(btc.id, btc.display_name, btc.icon);
```

```
{ id: 'bitcoin', kind: 'asset' }
bitcoin Bitcoin https://catalogue.tribulnation.com/icons/asset/bitcoin.svg
```

The client fetches from the API above. See the [JS README](js/README.md) for instruments, platforms and the exported types.

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

`Catalogue.load()` downloads the public catalogue on first use and caches it locally. It checks for changes at most once a day with a conditional request, re-downloads only when the data changed, and keeps the last good copy if the site is unreachable.

```python
catalogue = Catalogue.load()             # use cache, refresh daily
catalogue = Catalogue.load(refresh=True) # force fresh download
catalogue = Catalogue.load('data')       # explicit local folder

catalogue = catalogue.maybe_refresh()    # long-running processes: cheap, returns self when unchanged
catalogue.digest                         # sha256 of the loaded data.zip

catalogue.asset_for('hyperliquid', 150)  # 'hyperliquid'
catalogue.perpetual_for('dydx', 'BTC-USD').base  # 'bitcoin'

catalogue.format_correlation('cctp', source_domain=4, nonce=12345)  # 'cctp:4:12345'
catalogue.parse_correlation('ibc:dydx:channel-0:42')  # ('ibc', {'sending_chain': 'dydx', ...})
catalogue.network_for_domain('cctp', 3)  # 'arbitrum'
```

### Pricing

`MarketData` fetches prices and market caps for catalogue assets from one or more external providers. It needs the `prices` extra:

```bash
pip install 'tribulnation-catalogue[prices]'
```

Requests are batched per provider and run in parallel. If a provider fails, assets fall back to the next configured provider that covers them. This example uses the ECB reference rates, which need no API key:

```python
import asyncio
from datetime import datetime
from tribulnation.catalogue import Catalogue, MarketData

async def main():
    catalogue = Catalogue.load()
    market = MarketData.new('iso4217', quote='usd')  # ECB reference rates, no key needed
    gbp = catalogue.assets['british-pound']

    stats, errors = await market.current_stats({'british-pound': gbp})
    print(round(stats['british-pound'].price, 4), errors)

    price, errors = await market.historical_price(gbp, datetime(2024, 1, 2))
    print(round(price.price, 4), price.time)

asyncio.run(main())
```

```
1.3122 {}
1.2645 2024-01-02 00:00:00
```

Pass several sources to combine them, for example `MarketData.new('coingecko', 'twelvedata', 'iso4217')`, and `current_stats(catalogue.assets)` to price every asset in one call. Each result is a `Stats(price, market_cap, time)`.

Assets with a `pegged_to` field (e.g. XAUT → gold, cbBTC → bitcoin) automatically inherit the pegged asset's price if no direct price is found.

Providers that need an API key read it from the environment:

| Provider | Source | Env var | Covers |
|---|---|---|---|
| CoinGecko | `'coingecko'` | `COINGECKO_PRO_API_KEY` or `COINGECKO_DEMO_API_KEY` | Crypto — price, market cap, history |
| CoinMarketCap | `'coinmarketcap'` | `COINMARKETCAP_API_KEY` | Crypto — price, market cap, history |
| Twelve Data | `'twelvedata'` | `TWELVEDATA_API_KEY` | Precious metals (XAU, XAG†), forex |
| Alpha Vantage | `'alphavantage'` | `ALPHAVANTAGE_API_KEY` | US stocks, USD forex, energy & agricultural commodities |
| FRED | `'fred'` | none | Daily reference series in USD: forex, oil, natural gas |
| Yahoo Finance | `'yahoo'` | none | Stocks‡, forex |
| ECB | `'iso4217'` | none | Daily euro reference rates for ~30 fiat currencies (ISO 4217 codes) |

† XAG requires a paid Twelve Data plan.

‡ Non-US listings come back in their local currency for now ([#201](https://github.com/tribulnation/catalogue/issues/201)).

Provider IDs have provider-specific semantics, especially for forex, commodities, and stock symbols. See [External IDs](docs/external.md) for the conventions.

---

## What's inside

### Assets
Canonical records keyed by slug (e.g. `bitcoin`, `usd-coin`). Each asset has a `display_name`, `symbol`, optional `icon`, `tags`, peg information for stablecoins and wrapped tokens, and external IDs mapping to third-party providers:

| Field | Provider |
|---|---|
| `coingecko` | CoinGecko asset ID |
| `coinmarketcap` | CoinMarketCap asset ID |
| `twelvedata` | Twelve Data symbol (e.g. `XAU/USD`) |
| `alphavantage` | Alpha Vantage typed ID (e.g. `stock:TSLA`, `forex:EUR`, `commodity:WTI`) |
| `fred` | FRED series ID (e.g. `DEXUSEU`, `inverse:DEXJPUS`) |
| `yahoo` | Yahoo Finance symbol (e.g. `AAPL`, `EURUSD=X`) |
| `iso4217` | ISO 4217 code of a fiat currency or precious metal (e.g. `CHF`, `XAU`) |

### Platforms
Trading venues and networks keyed by slug (e.g. `binance`, `ethereum`). Covers CEX, DEX, and blockchain platforms. Blockchains carry `namespace`, `chain_id`, `native_asset`, and EVM/SVM `category`.

### Instruments
Spot pairs, margin pairs (spot traded on borrowed funds), perpetual futures, debt positions, and liquidity pools — each referencing canonical asset IDs. Maps exchange-specific tickers to the catalogue's canonical identifiers.

### Translations
Per-platform display-name mappings for assets and networks. Resolves what a given exchange calls `BTC/USDT` into `('bitcoin', 'tether')`.

### Icons
SVG icons for assets, platforms, and networks, organized under `icons/asset/`, `icons/platform/`, and `icons/network/`. All icons are **square and maskable** — they include a full square background and are designed to be displayed cropped to a circle or rounded square. API responses include absolute icon URLs.

### Spam
Known spam token addresses per chain, with optional source and reported timestamp.

### Protocols
Cross-chain protocols (`axelar`, `cctp`, `gofast`, `hlbridge`, `ibc`, `lighter`, `relay`) keyed by id. Each defines a **correlation key**: a template such as `cctp:{source_domain}:{nonce}` with typed fields, which both sides of one cross-chain movement can compute independently so they can be linked. Protocol data stays in the entry, e.g. CCTP's domain → network table. Keys are built and checked with `format_correlation` / `parse_correlation`.

---

## Status

The clients are at 0.x: their APIs can still change between minor versions, and the [release notes](https://github.com/tribulnation/catalogue/releases) list each change. The data changes often, but ids stay valid. Questions and wrong mappings go in [issues](https://github.com/tribulnation/catalogue/issues).

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

## License

MIT, see [LICENSE](LICENSE).
