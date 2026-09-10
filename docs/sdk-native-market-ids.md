# SDK native exchange and market IDs

This migration aligns namespaces and missing asset-symbol translations, not exact
listing coverage. It separates nine verified Classic coin listings from the 19
existing UTA coin entries. It infers no delistings.

| Venue | Exchange migration | Market-ID migration | Entries |
| --- | --- | --- | --- |
| Binance | `perp` → `usdm` | None | 193 |
| MEXC | Explicit `perp` instead of a missing field | None | 91 |
| Coinbase | `perp` → `intx` | `BTC-PERP` → `BTC-PERP-INTX` | 97 |
| Bitget UTA coin | `coin` | Restore/retain native `*_CM` symbols | 19 |
| Bitget Classic coin | `coin-classic` | Separate native Classic symbols, e.g. `BTCUSD` | 9 |

Coinbase IDs are Advanced Trade product IDs, not the bare International Exchange
instrument IDs. Its trading-page URLs also require the full `-PERP-INTX` product ID;
the previous suffix-stripping URL rule was incorrect. Bitget coin page
URLs retain `_CM`, which is also part of UTA native symbols, though absent from
Classic API symbols. Classic entries have no URL pending a verified Classic route;
the generator must not send them to the UTA instrument instead.

Live checks on September
10, 2026 found all ten entries missing from Classic in the UTA public instruments
listing, online with native `*_CM` symbols. UTA includes all 19 Catalogue coin
perpetuals. These are not stale Catalogue entries.

Bitget has [scheduled the remaining nine Classic coin perpetuals for retirement
on September 17, 2026](https://www.bitget.com/support/articles/12560603893788).
The accepted correction is coexistence: `bitget:coin` uses UTA native `*_CM` IDs;
`bitget:coin-classic` uses the Classic symbols. Catalogue entries preserve both
identities. Mark the Classic entries delisted after confirmed retirement, removing
any trading URLs; do not rename their historical IDs into UTA IDs. The SDK adapters
still need implementation and qualification before coordinated deployment.

The UTA listing currently fails Typed validation on delivery rows with an empty
`fundInterval`; the upstream correction is pending. UTA coin order quantities are
in quote units, not base units, so the SDK's fixed base-unit `Rules.step_size`
also needs an explicit contract decision. Neither issue is resolved by renaming.

The SDK release checks validate exchange/kind and native ID conventions. Rules
base/quote are checked for shared instruments; missing Catalogue instruments are
reported as deferred coverage, not passing observations or release blockers.

Consumer migration must update stored qualified IDs together with SDK deployment.
No SDK aliases, asset changes or automatic production-data migration are introduced.

It also adds 48 previously checked native symbol mappings to existing assets:
23 dYdX, 14 Bitget, and 11 MEXC. These let shared instruments' rules base/quote
translate without inventing new asset identities. dYdX uses USDC for quote and
fees, while retaining native `*-USD` market names. No global USD-to-USDC mapping
is introduced.

## Hyperliquid quote exceptions

The standard HYPE and PURR perpetuals now use `quote: usd-coin`, as specified by
[Hyperliquid](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/contract-specifications).
Their settlement remains USDC. Other native perpetuals retain their USDT quote;
builder-deployed markets are unchanged pending independent denomination checks.
