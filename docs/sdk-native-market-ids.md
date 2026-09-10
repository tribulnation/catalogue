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
instrument IDs. Its trading-page URLs continue to use the latter. Bitget coin page
URLs likewise retain the web-only `_CM` suffix. The URL generator implements these
differences; a URL is not an API market ID.

The ten Bitget entries absent from the prior Classic listing are still unresolved
coverage findings. Their names now follow the same API convention as the verified
entries; this is not a claim that they have become listed. Coverage across these
venues will be investigated separately, as agreed with the SDK maintainer.

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
