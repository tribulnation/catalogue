# Pending market additions: local SDK check

Checked on 2026-09-12 against Catalogue main `0078267` and SDK main
`afb7bfd`. This is a scoped maintainer observation, not release qualification
or a claim of complete venue coverage.

## Added inventory

| Venue | Spot additions | Perpetual additions | Exchange IDs |
| --- | ---: | ---: | --- |
| Binance | 15 | 0 | `spot` |
| Bitget | 9 | 8 | `spot`, `usdt` |
| Bybit | 6 | 5 | `spot`, `perp` |
| Coinbase | 11 | 0 | `spot` |
| Bit2Me | 10 | 0 | `spot` |

All 64 added keys appeared verbatim in live SDK `exchange.markets()` output
under the declared exchange and market kind. Bitget's USDT drafts were changed
from the obsolete `perp` exchange ID to `usdt`.

Added 23 native-asset translations: seven Binance, eleven Coinbase, and five
Bybit (`KSM`, `MOVE`, `SUSHI`, `TAIKO`, `WOO`). Bitget's relevant translations
and Bit2Me's currencies were already on main. Every referenced canonical asset
already exists; this change introduces no new asset identity.

## What was checked

1. Called the SDK's venue `exchanges()` and each affected exchange's `markets()`
   on mainnet, checking exact IDs rather than stripping exchange prefixes.
   Binance discovered 3,698 spot markets; Bitget 1,761 spot and 787 USDT
   perpetuals; Bybit 538 spot and 829 perpetuals; Coinbase 931 spot; Bit2Me 286
   spot. Counts describe those observations, not a promised stable inventory.
2. Inspected native listing metadata for Binance, Bitget, Bybit and Coinbase.
   Their base/quote symbols match the proposed translations. Binance's added
   records were `TRADING`, Bitget's spot records `online` and USDT records
   `normal`, Bybit's records `Trading`, and Coinbase's records `online` with
   `trading_disabled=false`. Bybit explicitly reports USDT settlement for the
   added perpetuals; Bitget records come from its `USDT-FUTURES` product.
3. Coinbase's authenticated Advanced Trade product catalogue explicitly names
   `VELO-USD` as **Velodrome Finance** and `SPX-USD` as **SPX6900**, not the S&P
   index. The other nine product base names also agree with their canonical
   assets. This uses upstream product metadata, not the removed SDK Rules
   base/quote fields. Coinbase metadata names also corroborate the overlapping
   Binance/Bybit tokens. Binance identifies [WOO Network](https://www.binance.com/en/research/projects/wootrade)
   and [Movement](https://www.binance.com/en/support/announcement/detail/601c0c23d12e40ee80310ac5e7c6369e);
   Bybit identifies [Taiko (TAIKO)](https://www.bybit.com/en/price/taiko/).
4. Bit2Me's listing reports the exact slash-delimited symbols, not separate
   canonical base/quote identities. Its existing Catalogue currency translations
   were reused. Eight added markets are `enabled`; `BTC/EURR` and `EUR/EURR`
   are **`frozen`**. They remain discoverable identities, not a claim that orders
   can currently be placed. Frozen is not interpreted as delisted.
5. Catalogue `scripts/validate.py` passed. SDK `sdk-dev catalogue check --path
   /path/to/this/data` passed translation-key shape checks. The existing
   `scripts/instrument_urls.py` generated 54 URLs for supported rules.

## Existing SDK tools and limits

1. `sdk-dev catalogue coverage market --accounts sdk.test.toml --path
   /path/to/catalogue/data --only coinbase` discovers SDK IDs and lists gaps.
   Repeat `--only` for other configured account IDs. Its gap matching accepts
   stripped exchange prefixes: it is a coverage report, not sufficient proof of
   the correct exchange namespace.
2. `sdk-dev test consistency <venue> --catalogue /path/to/catalogue/data`
   checks exact exchange/kind/native-ID conventions plus sampled market-data
   behavior. Missing Catalogue market coverage is deferred, not a release
   blocker. It intentionally does not independently verify canonical base/quote
   identity; that is Catalogue territory. No SDK contract or gate was changed.
3. This scoped pass used live SDK discovery and inspected upstream metadata;
   it did not rerun all market, Wallet, Earn or Report behavior suites, generate
   fresh release evidence, or claim universal current trading availability.

## Deferred findings

1. The original Bitget spot draft `ALTUSDT` was absent from live discovery and
   is **not added**. No case-insensitive ALT-like spot symbol was present.
   Bitget's [AltLayer listing announcement](https://www.bitget.com/support/articles/12560603804190)
   explicitly calls that asset `$ALT`, illustrating why the old draft must not
   be accepted by symbol inference. No replacement or delisting was guessed.
2. Broad all-exchange Bitget discovery raised `ValidationError`; targeted spot
   and USDT discovery both passed. This pass does not qualify the other Bitget
   product lines or relabel that failure as success.
3. The URL generator has no verified Bit2Me rule, so its ten added entries have
   no URL. No guessed rule was introduced. Generated URLs elsewhere were not
   browser-verified; instrument-page verification remains a separate check.
4. Already-merged Aave mappings, native-ID corrections and translation drafts
   were excluded. No stale local file replaced modern main wholesale.

Credentials and raw private responses are not included in this record.
