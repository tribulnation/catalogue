# AGENTS.md

NEVER INCLUDE YOURSELF AS AUTHOR IN GIT COMMITS, OR ELSEWHERE.

## Schema

The schema is defined in `lib/src/tribulnation/catalogue/data/schema.py`.

## Scope
These instructions apply to the repository at `/home/m4rs/github/tribulnation/catalogue`.

## Local guidance
- When running validation (or other local scripts), use the repo virtualenv: `PYTHONPATH=lib/src .venv/bin/python scripts/validate.py`.

## Asset and platform metadata

Every new asset and platform record must include a meaningful English description
in `about.en` and at least one official project or issuer link in `urls`. Verify
the project identity and the page content; a successful HTTP response alone is
not enough. Use accurately labeled documentation, source-code or official
community links when no usable homepage exists. Do not use guessed domains,
aggregator listing pages, or generic exchange-listing descriptions as substitutes.
Keep metadata identical when the same record appears in multiple venue PRs.

Every new asset must account for its external provider IDs in `external`,
matched by project identity, issuer or contract rather than ticker alone. For
crypto, stablecoin and tokenized-asset records, search both CoinGecko and
CoinMarketCap and include every independently verified exact identity; other
records need at least one supported provider ID. Never substitute the underlying
asset for a wrapper, bridge claim or receipt.

A provider with no exact listing is fine, but the search must be shown: add an
`"<asset>:<provider>"` entry to `scripts/external_id_exceptions.json` saying what
was searched (contract, issuer, chain, symbol) and why the near matches are a
different asset. Run `scripts/check_new_assets.py --base <base-commit>`; it fails
on any required provider (or, for other records, on having no provider at all)
with neither an ID nor a justification, and on justifications
left behind once an ID is added.

## Instrument URLs

Spot and perpetual instruments carry a `url` field pointing at the platform's trading page for that instrument, e.g. `https://app.hyperliquid.xyz/trade/BTC` for Hyperliquid's BTC perpetual. It is optional in the schema, but every listed instrument on a supported platform should have one. Delisted instruments must not have one — their trading pages are gone — and validation enforces that.

Do not write them by hand. `scripts/instrument_urls.py` derives them from the instrument ID (splitting concatenated IDs such as `1INCHUSDT` into base/quote symbols where the platform's URLs need them). Run it after adding instruments:

```sh
PYTHONPATH=lib/src .venv/bin/python scripts/instrument_urls.py
```

It only fills in missing URLs, so hand-written ones survive; pass `--overwrite` to regenerate everything. When adding a platform, add its URL rule to `SPOT_RULES` / `PERPETUAL_RULES` in that script; instruments on platforms without a rule are left without a `url`.

## Quanto perpetuals

A perpetual's `quote` is the currency its price is in, even when the venue labels
the contract `USDT`. Binance `HK0700USDT` prints Tencent's HK$ share price, so its
`quote` is `hong-kong-dollar` and its `settlement` is `tether`. Compare the venue's
price with the underlying's local price before choosing `quote`; the same share
can also trade USD-priced on the same venue (Binance `TENCENTUSDT`).

When `quote` and `settlement` are different currencies, set `quanto`:

- `true`: P&L accrues 1 `settlement` unit per 1 `quote` price point, per unit of
  `base` times `multiplier`, with no exchange rate applied. Notional in
  `settlement` is size x multiplier x price.
- `false`: the venue converts `quote` P&L to `settlement` at the exchange rate.

Evidence is the venue's own notional: turnover or open interest in the settlement
asset equal to size x contract size x price (MEXC `amount24`, QFEX
`open_interest_usd`, Lighter `open_interest_usd`) means `true`. Validation requires
the field on every stock perpetual priced in a fiat currency other than the
settlement's, and rejects it when both are the same currency.

## Perpetual quote is never the settlement by default

A perpetual's `quote` is the currency its **index** tracks; `settlement` is the
coin it pays out in. Never copy the settlement (or the venue's collateral label)
into `quote`. On Lighter and Hyperliquid every perpetual settles in USDC (or a
HIP-3 dex's own collateral) while the index is not USDC:

- Lighter: crypto (including prelaunch tokens such as XTEN, and delisted crypto
  markets) -> `quote: tether`; stocks, ETFs, commodities, FX and pre-IPO markets
  -> `quote: usd`. Lighter converts HK$/CN¥/KRW/JPY share prices to USD (TENCENT
  reads 53 when 0700.HK is HK$420), so Asian stock markets are `usd` too, unless
  the price really is local (the delisted `SAMSUNG` `140` printed 219,500 KRW:
  `south-korean-won` with `quanto`). Check `priceOracleInfo` (docs/sdk-native-market-ids.md, "Lighter index sources") and the
  [market specifications](https://docs.lighter.xyz/trading/real-world-assets-rwas/market-specifications).
- Hyperliquid: `quote: tether` (HYPE and PURR are the documented USDC
  exceptions).

`scripts/check_perp_quotes.py` (run in CI through `lib/tests/test_perp_quotes.py`) fails on any Lighter or Hyperliquid
perpetual with `quote: usd-coin` that `scripts/perp_quote_exceptions.json` does
not list with evidence. A market whose sources are `internal_price` (Lighter's
order-book EMA: pre-IPO, prelaunch, or a stock outside its trading hours) still
gets the quote of its kind, not USDC.

## Blockchain category and chain id

`namespace` and `chain_id` together form the chain's
[CAIP-2](https://github.com/ChainAgnostic/namespaces) id: `eip155:1`,
`cosmos:cosmoshub-4`, `polkadot:91b171bb158e2d3848fa23a9f1c25182`. Derive the
reference by that namespace's `caip2.md` and read it back from the live chain
(`eth_chainId`, Cosmos `node_info.network`, block-0 hash); a registry entry alone
is not enough. `chain_id` is an integer only under `eip155`. Cosmos chain ids
outside `[-a-zA-Z0-9]{1,32}` use the `hashed-` form.

`category` says how the chain addresses tokens and accounts (`evm`,
`cosmos-sdk`, `substrate`, `utxo`, `move`, `svm`, `antelope`); leave it unset
when none fits. A chain running two environments gets one record per
environment, as with `kava` / `kava-evm` and `sei` / `sei-evm`.
docs/reports/blockchain-network-ids-2026-09-23.md records the evidence.

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

Cases where the obvious mapping produces a wrong price or a double-counted
balance are recorded in [docs/asset-traps.md](docs/asset-traps.md). Check it
before adding a stablecoin or a tokenised RWA.

## Searching Instruments

Use the guides below to find instrument IDs for supported platforms:

### Asset Translations

Asset translations map platform-native asset IDs or symbols to catalogue asset IDs. Add or update `data/asset_translations/<platform>.json` when a platform uses an asset identifier that is not already mapped, or when a symbol is ambiguous and needs a canonical asset.

For symbol-based platforms such as MEXC and dYdX, translation keys are usually exchange symbols like `VVV`, `DYDX`, or `USDT`. For Hyperliquid spot, translation keys are numeric token indexes from `spotMeta.tokens[].index`; do not use spot pair names as translation keys there. Hyperliquid perpetual instruments usually do not need asset translations because the instrument ID uses the `meta.universe[].name` value directly.

Translation values must be existing catalogue asset IDs from `data/assets/<id>.json`. Run validation after adding translations.

### dYdX

Perpetual assets have shape `<DYDX_ID>-USD`. You can enumerate markets via the API https://indexer.dydx.trade/v4/perpetualMarkets

### gTrade

`data/instruments/perpetual/gtrade.json` is generated; do not edit it by hand.
`scripts/gtrade.py` builds it from gTrade's backend
(`https://backend-<chain>.gains.trade/trading-variables`, one per chain), recorded
in `scripts/gtrade_fixture.json`. There is one instrument per chain, collateral
vault and pair (`arbitrum-usdc:BTC/USD`), since each vault has its own open
interest, funding and borrowing.

```sh
# re-record the backend and rebuild the file
PYTHONPATH=lib/src .venv/bin/python scripts/gtrade.py --refresh
```

Base and quote assets come from `data/asset_translations/gtrade.json` (gTrade ticker
-> asset id), and settlement from the collateral's contract address in the chain's
asset translations. A newly listed ticker that is not mapped fails the run with the
list of missing tickers; map it (matched by price and identity, never by ticker
alone) or add it to `EXCLUDED` in the script with a reason. `lib/tests/test_gtrade.py`
fails CI when the committed file differs from what the fixture gives.

### Hyperliquid

Perpetual instrument IDs use Hyperliquid's `coin` name from the `meta` response. Enumerate perpetual markets with:

```sh
curl -L https://api.hyperliquid.xyz/info \
  -H 'Content-Type: application/json' \
  --data '{"type":"meta"}'
```

For standard perpetuals, add entries to `data/instruments/perpetual/hyperliquid.json` using the `universe[].name` value as the instrument ID, e.g. `HYPE` or `VVV`. In this catalogue, Hyperliquid perpetuals use `quote: "tether"` and `settlement: "usd-coin"` unless the specific venue or market requires a different settlement asset; `quote: "usd-coin"` fails CI unless listed in `scripts/perp_quote_exceptions.json` (see "Perpetual quote is never the settlement by default").

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
