# AGENTS.md

NEVER INCLUDE YOURSELF AS AUTHOR IN GIT COMMITS, OR ELSEWHERE.

## Schema

The schema is defined in `lib/src/tribulnation/catalogue/schema.py`.

## Scope
These instructions apply to the repository at `/home/m4rs/github/tribulnation/catalogue`.

## Local guidance
- When running validation (or other local scripts), use the repo virtualenv: `PYTHONPATH=lib/src .venv/bin/python scripts/validate.py`.

## Searching Instruments

Use the guides below to find instrument IDs for supported platforms:

### Asset Translations

Asset translations map platform-native asset IDs or symbols to catalogue asset IDs. Add or update `data/asset_translations/<platform>.json` when a platform uses an asset identifier that is not already mapped, or when a symbol is ambiguous and needs a canonical asset.

For symbol-based platforms such as MEXC and dYdX, translation keys are usually exchange symbols like `VVV`, `DYDX`, or `USDT`. For Hyperliquid spot, translation keys are numeric token indexes from `spotMeta.tokens[].index`; do not use spot pair names as translation keys there. Hyperliquid perpetual instruments usually do not need asset translations because the instrument ID uses the `meta.universe[].name` value directly.

Translation values must be existing catalogue asset IDs from `data/assets/<id>.json`. Run validation after adding translations.

### dYdX

Perpetual assets have shape `<DYDX_ID>-USD`. You can enumerate markets via the API https://indexer.dydx.trade/v4/perpetualMarkets

### Hyperliquid

Perpetual instrument IDs use Hyperliquid's `coin` name from the `meta` response. Enumerate perpetual markets with:

```sh
curl -L https://api.hyperliquid.xyz/info \
  -H 'Content-Type: application/json' \
  --data '{"type":"meta"}'
```

For standard perpetuals, add entries to `data/instruments/perpetual/hyperliquid.json` using the `universe[].name` value as the instrument ID, e.g. `HYPE` or `VVV`. In this catalogue, Hyperliquid perpetuals generally use `quote: "tether"` and `settlement: "usd-coin"` unless the specific venue or market requires a different settlement asset.

HIP-3 builder-deployed perpetuals use the same API, but Hyperliquid identifies them with a DEX prefix. Use instrument IDs shaped `<DEX>:<COIN>`, e.g. `hyna:SOL` or `flx:XMR`, and set the instrument `exchange` field to the DEX prefix, e.g. `"exchange": "hyna"`. Check the market's collateral/settlement before adding it; HIP-3 examples in this repo include settlement assets such as `ethena-usde` and `hyperliquid-usd`, not only `usd-coin`.

Spot instrument IDs use Hyperliquid spot names from the `spotMeta` response. Enumerate spot markets with:

```sh
curl -L https://api.hyperliquid.xyz/info \
  -H 'Content-Type: application/json' \
  --data '{"type":"spotMeta"}'
```

For canonical named spot pairs, use the `universe[].name` value directly, e.g. `PURR/USDC`. For pairs represented as `@<index>` in `spotMeta.universe`, keep the repo convention `<BASE>/<QUOTE>:<index>`, e.g. `UBTC/USDC:142` or `HYPE/USDT0:207`. Hyperliquid spot asset translations in `data/asset_translations/hyperliquid.json` are keyed by the numeric spot token index from `spotMeta.tokens[].index`.

### MEXC

Spot instrument IDs use MEXC's `symbol` from the spot exchange-info endpoint, usually concatenated as `<BASE><QUOTE>`, e.g. `VVVUSDT`. Enumerate all spot markets with:

```sh
curl -L https://api.mexc.com/api/v3/exchangeInfo
```

To check one symbol directly, pass `symbol`:

```sh
curl -L 'https://api.mexc.com/api/v3/exchangeInfo?symbol=VVVUSDT'
```

Add confirmed spot pairs to `data/instruments/spot/mexc.json` and set `"exchange": "spot"`. Use `baseAsset` and `quoteAsset` from the API response to decide the canonical `base` and `quote` assets. If a new MEXC asset symbol is not already translated, add it to `data/asset_translations/mexc.json`, e.g. `"VVV": "venice-token"`.

Perpetual instrument IDs use MEXC contract symbols from the contract detail endpoint, usually shaped `<BASE>_<QUOTE>`, e.g. `VVV_USDT`. Enumerate all perpetual markets with:

```sh
curl -L https://contract.mexc.com/api/v1/contract/detail
```

To check one contract directly, pass `symbol`:

```sh
curl -L 'https://contract.mexc.com/api/v1/contract/detail?symbol=VVV_USDT'
```

Add confirmed perpetuals to `data/instruments/perpetual/mexc.json`. Use `baseCoin`, `quoteCoin`, and `settleCoin` from the API response to map `base`, `quote`, and `settlement`.
