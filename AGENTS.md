# AGENTS.md

NEVER INCLUDE YOURSELF AS AUTHOR IN GIT COMMITS, OR ELSEWHERE.

## Schema

The schema is defined in `lib/src/tribulnation/catalogue/data/schema.py`.

## Scope
These instructions apply to the repository at `/home/m4rs/github/tribulnation/catalogue`.

## Local guidance
- When running validation (or other local scripts), use the repo virtualenv: `PYTHONPATH=lib/src .venv/bin/python scripts/validate.py`.

## EVM addresses

`data/asset_translations/<chain>.json` maps an on-chain identifier to a catalogue
asset id. For an EVM chain the key is the token's **EIP-55 checksummed contract
address**, or the literal `native` for the chain's gas coin. Two rules decide
which asset an address maps to. They exist because a portfolio has to be able to
tell apart things that can lose their peg to each other.

### 1. An issuerless coin is only ever reachable as `native`

BTC and ETH have no issuer. Nobody can deploy an official ERC-20 for them, so
**every** EVM token claiming to represent one is somebody else's IOU, backed by a
custodian who can fail. Those never map to `bitcoin` or `ethereum` — each gets its
own asset, with `pegged_to` naming what it tracks:

| Address | Asset | Not |
| --- | --- | --- |
| `0x2260FAC5…` WBTC on ethereum | `wrapped-bitcoin` | ~~`bitcoin`~~ |
| `0xcbB7C000…` cbBTC on ethereum | `coinbase-wrapped-bitcoin` | ~~`bitcoin`~~ |
| `0x7130d2A1…` BTCB on bnb-chain | `binance-bitcoin` | ~~`bitcoin`~~ |
| `0xC02aaA39…` WETH on ethereum | `wrapped-ether` | ~~`ethereum`~~ |
| `0x2170Ed08…` ETH on bnb-chain | `binance-peg-ethereum` | ~~`ethereum`~~ |

`native` is the only key that may name them, and only where the coin really is the
gas token: `"native": "ethereum"` is right on ethereum, arbitrum, base and optimism.

For a coin that *does* have an issuer — VANA, POL, CRO, MNT, ATOM, XRP, ADA — ask
who deployed the token. The issuer's own canonical deployment is the same credit as
the coin, so it collapses into the coin's asset: the VANA OFT at
`0x7ff7fa94…`, live at that one address on six chains, is `vana` everywhere. A
third party's wrapper is a different credit and splits off:

| Address | Asset | Not |
| --- | --- | --- |
| `0x0eb3a705…` Cosmos Token on bnb-chain | `binance-peg-cosmos` | ~~`cosmos`~~ |
| `0x76a797a5…` Wrapped TON Coin on bnb-chain | `binance-peg-toncoin` | ~~`toncoin`~~ |
| `0x1D2F0da1…` XRP on bnb-chain | `binance-peg-xrp` | ~~`xrp`~~ |

The test is *who is on the hook if the backing goes missing*, not which bridge the
token crossed.

### 2. A token spans its deployments, unless two of them coexist

An asset that is *already* an ERC-20 keeps **one** asset id across every chain and
every bridge. Circle's USDC on ethereum, the OP-stack bridged USDC on base and the
Binance-Peg USDC on bnb-chain are all `usd-coin`. Likewise bridged WETH, DAI, WBTC
and wstETH on every L2 stay `wrapped-ether`, `dai`, `wrapped-bitcoin`,
`wrapped-staked-ether` — the chain's own bridge is the only custodian, so there is
nothing for a holder to choose between.

The exception is **coexistence**: when a chain carries two deployments of the same
asset at once, a holder can hold either, they trade separately, and they can
depeg from each other. Then the non-canonical one splits off:

| Chain | Address | Asset |
| --- | --- | --- |
| arbitrum | `0xaf88d065…` USDC | `usd-coin` |
| arbitrum | `0xFF970A61…` USDC.e | `bridged-usd-coin` |

Note what this rule is **not**. CoinGecko issues a separate coin id per
*deployment* (`l2-standard-bridged-weth-base`, `polygon-pos-bridged-dai`), which is
finer than this catalogue wants: a portfolio should show one WETH balance, not one
per chain. Use CoinGecko to discover addresses, not to decide asset identity.

### Verifying an address

Never take an address from a data feed alone — feeds carry stale, renamed and
plain wrong entries. Read it back from the chain before it lands:

- `eth_getCode` must return bytecode. A feed pointing at an address with nothing
  deployed on that chain is a copied-from-another-chain error.
- `symbol()` and `decimals()` must return sane values.
- The symbol must relate to the asset. `W`/`w` prefixes, `.e`/`0`/`b` suffixes and
  chain-prefixed Aave names are expected; anything else needs a human.

Decimals are per-address, not per-asset — the same asset can have different
decimals on different chains.

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
