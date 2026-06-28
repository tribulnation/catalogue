# Core Messaging

## Tagline

> Every exchange has its own language. Tribulnation Catalogue speaks them all.

## One-liner

Tribulnation Catalogue maps the inconsistent IDs, symbols, and network names that exchanges and data APIs throw at you into a single typed, canonical record — with icon and pricing included.

## Elevator pitch

Every exchange invents its own identifiers: Binance calls the network `BSC`, MEXC calls it `BNB Smart Chain(BEP20)`, Bitget calls it `BEP20`, Hyperliquid calls Bitcoin `197`. Tribulnation Catalogue is the translation layer — feed it any exchange's raw asset or network string and get back a canonical, enriched record: ID, display name, symbol, icon, peg info, and pricing. One open catalogue, every provider resolved.

## Key claims (reusable bullets)

- Normalizes asset and network IDs across Binance, Bybit, MEXC, Bitget, Kraken, KuCoin, dYdX, Hyperliquid, and more
- Covers crypto assets, forex, commodities, and blockchain networks
- Static JSON API — no auth, no rate limits, served from GitHub Pages
- Typed Python and TypeScript clients
- Pricing via CoinGecko, CoinMarketCap, Twelve Data, and Alpha Vantage — one SDK, automatic routing
- Open source (MIT)

---

## The table

The single most compelling demo — real data, all verified from the catalogue.

### Networks: same chain, six different strings

| Exchange | Raw string | Catalogue |
|---|---|---|
| Binance | `"BSC"` | `bnb-chain` |
| MEXC | `"BNB Smart Chain(BEP20)"` | `bnb-chain` |
| Bitget | `"BEP20"` | `bnb-chain` |
| KuCoin | `"BSC"` | `bnb-chain` |
| Bybit | `"BSC (BEP20)"` | `bnb-chain` |
| Kraken | `"BNB Chain"` | `bnb-chain` |

### Avalanche — four strings, zero overlap

| Exchange | Raw string | Catalogue |
|---|---|---|
| MEXC | `"AVAX_CCHAIN"` | `avalanche` |
| Bitget | `"AVAXC-Chain"` | `avalanche` |
| Binance | `"AVAX"` | `avalanche` |
| Kraken | `"Avalanche C-Chain"` | `avalanche` |

### Assets: Bitcoin across exchanges

| Exchange | Raw string | Catalogue |
|---|---|---|
| Most exchanges | `"BTC"` | `bitcoin` |
| Kraken | `"XXBT"` | `bitcoin` |
| Hyperliquid | `197` | `bitcoin` |

---

## Channel notes

- **HN / README**: plain table, no decoration — the raw strings do the work
- **Twitter/X**: styled dark-background image, monospace font for exchange strings
- **Tone**: never mock exchanges — frame it as "the ecosystem evolved organically"; Tribulnation Catalogue is the glue
