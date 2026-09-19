# Deribit market and earn identities — 2026-09-19

Adds all 19 SDK-supported spot pairs and 90 of 126 supported linear perpetuals,
with exact `spot` / `perp` exchange IDs. Adds 52 asset aliases, including distinct
BUIDL and USYC fund assets. Base: Catalogue `720d172`; SDK: Deribit 0.3.0 / core 2.2.0.

## Identity evidence

1. Active product selection follows the SDK: spot, or perpetual linear futures
   whose native quote and settlement currencies agree. Inverse contracts, dated
   futures, options and combinations are outside this addition.
2. Existing currency aliases are reused. New crypto identities are checked through
   Deribit's explicit Coinbase index references and asset UUIDs, Coinbase currency
   names, and [Coinbase's product specifications](https://help.coinbase.com/en/international-exchange/perpetual-futures-basics/perpetual-futures-product-specifications).
   In particular, the perpetual specification identifies `LIT` as Lighter; the
   legacy Exchange currency list still calls its different `LIT` asset Litentry.
   `CFX` and `DYDX` are identified by their named perpetual specifications.
3. [Deribit's RWA specifications](https://support.deribit.com/hc/en-us/articles/38325634622493-RWA-Perpetual)
   and native `underlying_type` distinguish equity and commodity references from
   crypto tokens. `META` is the equity Meta Platforms, not the similarly named
   crypto asset. GOLD/SILVER and the oil contracts reference commodities rather
   than wrapped/tokenized collateral.
4. `1000BONK`, `1000PEPE` and `1000SHIB` use canonical BONK/PEPE/SHIB assets with
   `multiplier: 1000`, corroborated by Coinbase's native `base_asset_multiplier`.
   These are price-index multipliers, not Deribit's minimum quantity/contract-size
   increments. They do not become unscaled global asset aliases.
5. [Deribit's yield-coin documentation](https://support.deribit.com/hc/en-us/articles/31424939199261-Yield-reward-bearing-coins)
   identifies the fund products. [BUIDL's issuer](https://securitize.io/blackrock/buidl)
   and [USYC's administrator](https://www.circle.com/usyc) establish separate fund
   identities. Neither is collapsed into USD, USDC or the other fund. USYC has no
   fixed-dollar `pegged_to` fallback; fund income accrues in its value. Provider IDs
   were checked by full name against CoinGecko's public coin list.
6. URLs come from `scripts/instrument_urls.py`. The official trading application's
   routes are `/spot/<instrument>` and `/futures/<instrument>`; USDC is not a
   separate path component. Coinbase-routed spot retains its Deribit venue identity.

## Remaining work

The companion JSON enumerates all 36 untranslated discovered perpetual IDs.
Their missing canonical records need further identity work; they are not mapped
using ticker similarity. This includes new crypto projects, equities, ETFs and
pre-IPO references. Discovery support does not itself qualify their identity.

All 52 retained earn observations now resolve their assets. Transfers still resolve
54 of 61 rows per direction: the seven remaining network IDs are SDK currency
fallbacks (`BUIDL`, `EURR`, `MATIC`, `SEI`, `STETH`, `USDE`, `USYC`). They are not
network identities. This is the SDK-owned source gap already recorded in
[Catalogue #122](https://github.com/tribulnation/catalogue/issues/122#issuecomment-5716869876).

Terminal integration, collection-policy review, release refresh and serving rebuilds
remain a later task. This PR does not certify routed candle or funding support.

## Coverage and validation

| Retained dataset | Rows | Resolved before | Resolved after |
| --- | ---: | ---: | ---: |
| earn_instruments | 52 | 50 | 52 |
| deposit_methods | 61 | 54 | 54 |
| withdrawal_methods | 61 | 54 | 54 |

These checks use the latest retained local observations on September 19. Resolution
requires asset, optional yield/fee asset, and (for transfers) network translations.
No Terminal collection, database changes, serving replay or deduplication was performed.

The [companion JSON](deribit-coverage-2026-09-19.json) records accepted identities, public source URLs,
native market evidence where applicable, and remaining identifiers.

1. Full Catalogue validation passes with `PYTHONPATH=lib/src .venv/bin/python scripts/validate.py`.
2. Instrument URLs are generated with the repository script; `git diff --check` passes.
3. Fresh credential-free SDK discovery, construction and ticker reads pass for every added market with response validation enabled.
4. All four existing instrument-URL regression tests pass.

The SDK consistency run and its offline fingerprint/policy verifier both pass.
Check statuses: `{"pass": 241}`. Explicit policy deferrals
are not resolved identities or exhaustive coverage. Reproduce from the SDK checkout:

```sh
.venv/bin/sdk-dev test consistency deribit --catalogue ../catalogue-sdk-markets/data --output /tmp/deribit-catalogue-review
.venv/bin/sdk-dev results verify /tmp/deribit-catalogue-review --catalogue ../catalogue-sdk-markets/data
```
