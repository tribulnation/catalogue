# SDK native exchange and market IDs

This migration aligns namespaces and missing asset-symbol translations, not current listing coverage. It adds no markets,
infers no delistings, and does not claim every existing entry is currently available.

| Venue | Exchange migration | Market-ID migration | Entries |
| --- | --- | --- | --- |
| Binance | `perp` → `usdm` | None | 193 |
| MEXC | Explicit `perp` instead of a missing field | None | 91 |
| Coinbase | `perp` → `intx` | `BTC-PERP` → `BTC-PERP-INTX` | 97 |
| Bitget coin | Already `coin` | Remaining `*_CM` → Classic API symbol without `_CM` | 10 |

Coinbase IDs are Advanced Trade product IDs, not the bare International Exchange
instrument IDs. Its trading-page URLs also require the full `-PERP-INTX` product ID;
the previous suffix-stripping URL rule was incorrect. Bitget coin page
URLs retain `_CM`, which is also part of UTA native symbols, though absent from
Classic API symbols. The URL generator currently handles the Classic convention.

**Bitget coin migration needs revision before merging.** Live checks on September
10, 2026 found all ten entries missing from Classic in the UTA public instruments
listing, online with native `*_CM` symbols. UTA includes all 19 Catalogue coin
perpetuals. These are not stale Catalogue entries.

Bitget has [scheduled the remaining nine Classic coin perpetuals for retirement
on September 17, 2026](https://www.bitget.com/support/articles/12560603893788).
The proposed correction is to source SDK `bitget:coin` public market data from UTA
and restore its native `*_CM` Catalogue IDs. That SDK/source decision and ID
revision are pending; the table above describes the current diff, not the final
recommended Bitget migration. Exact listing coverage remains a separate pass.

The SDK release checks validate exchange/kind and native ID conventions. Rules
base/quote are checked for shared instruments; missing Catalogue instruments are
reported as deferred coverage, not passing observations or release blockers.

Consumer migration must update stored qualified IDs together with SDK deployment.
No SDK aliases, asset changes or automatic production-data migration are introduced.

It also adds 48 previously checked native symbol mappings to existing assets:
23 dYdX, 14 Bitget, and 11 MEXC. These let shared instruments' rules base/quote
translate without inventing new asset identities. dYdX uses USDC for quote and
fees, while retaining native `*-USD` market names. No global USD-to-USDC mapping
is introduced, and Catalogue quote/settlement fields are unchanged.
