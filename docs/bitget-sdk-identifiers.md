# Bitget product identities

The SDK uses Bitget Classic public API symbols, qualified by product line:

| Exchange ID | Bitget product type | Example market ID |
| --- | --- | --- |
| `spot` | `SPOT` | `BTCUSDT` |
| `usdt` | `USDT-FUTURES` | `BTCUSDT` |
| `usdc` | `USDC-FUTURES` | `BTCPERP` |
| `coin` | `COIN-FUTURES` | `BTCUSD` |

`perp` is no longer an exchange ID for Bitget. The instrument remains a perpetual;
the exchange ID distinguishes its product line. Consumers storing qualified IDs
must migrate the exchange component, including historical records.

## Verification on 2026-09-10

Public contract listings at
`https://api.bitget.com/api/v2/mix/market/contracts?productType=<PRODUCT>`
were compared with this Catalogue snapshot. Delivery contracts were excluded.

1. All 139 USDT entries and all 43 USDC entries matched native symbols and translated
   base/quote assets. Only their exchange IDs change.
2. Nine coin entries matched after removing the web/UTA `_CM` suffix:
   `ADAUSD`, `AVAXUSD`, `BTCUSD`, `DOGEUSD`, `ETHUSD`, `LINKUSD`, `NEARUSD`,
   `SOLUSD`, and `XRPUSD`. Their translated base/quote assets also matched.
   Their Catalogue keys now use these verified Classic API symbols.
3. The other ten coin entries were absent from that Classic perpetual listing:
   `AAVEUSD_CM`, `APTUSD_CM`, `BCHUSD_CM`, `DOTUSD_CM`, `ETCUSD_CM`,
   `FILUSD_CM`, `LTCUSD_CM`, `SUIUSD_CM`, `UNIUSD_CM`, and `XLMUSD_CM`.
   They retain their existing keys and metadata, except for classification under
   `coin`. They are unresolved SDK coverage mismatches, not verified delistings.
4. Coin trading-page URLs retain `_CM`; the URL generator keeps this web convention
   separate from API identity. This check did not verify rendered trading pages.

This migration does not add every market from the venue, certify SDK release
readiness, or alter private-account coverage. In particular, the live Typed client
currently rejects empty numeric fields in delivery rows from the coin contract
listing, before the SDK can filter them. That response-validation blocker and the
ten unresolved Catalogue IDs must remain visible during qualification.
