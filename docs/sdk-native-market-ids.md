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
any trading URLs; do not rename their historical IDs into UTA IDs.

UTA SDK support is explicitly deferred in [SDK issue #32](https://github.com/tribulnation/sdk/issues/32):
its native USD-sized quantities do not fit the current base-unit Rules contract.
The `coin` Catalogue identity remains reserved for UTA, but the SDK does not
advertise it. Classic `coin-classic` support remains in scope. The separate Typed
delivery validation fix is prepared for release in [Typed PR #124](https://github.com/tribulnation/typed/pull/124).

The SDK release checks validate exchange/kind and native ID conventions. Base/quote
identity is Catalogue-owned: `Rules.base/quote` and their translated-rules check
are retired. Independent upstream asset checks belong to a later Catalogue pass.
Missing instruments are deferred coverage; UTA coin is a distinct explicit capability
exclusion. Neither is a passing observation or an inferred delisting.

Consumer migration must update stored qualified IDs together with SDK deployment.
No SDK aliases, asset changes or automatic production-data migration are introduced.

It also adds 48 previously checked native symbol mappings to existing assets:
23 dYdX, 14 Bitget, and 11 MEXC. These preserve verified native symbol mappings
without inventing new asset identities. dYdX uses USDC for quote and
fees, while retaining native `*-USD` market names. No global USD-to-USDC mapping
is introduced.

## Hyperliquid quote exceptions

The standard HYPE and PURR perpetuals now use `quote: usd-coin`, as specified by
[Hyperliquid](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/contract-specifications).
Their settlement remains USDC. Other native perpetuals retain their USDT quote;
builder-deployed markets are unchanged pending independent denomination checks.

## Perpetual quote is the index currency

A perpetual's `quote` is the currency its index price tracks. `settlement` is the
collateral it pays out in, which can differ: Hyperliquid's native perpetuals
track USDT and settle in USDC, so they carry `quote: tether`,
`settlement: usd-coin`.

Lighter's crypto perpetuals follow the same pattern and now use `quote: tether`;
their settlement stays USDC. This was measured from recorded index prices
between October 20 and 26, 2026, 17:10 UTC, when USDT traded about 12.8 bps
below USD (interquartile range 11.2 to 13.9), which separates the two cleanly:

| Market | vs USDT index | vs USD | Reading |
| --- | --- | --- | --- |
| Lighter BTC (`1`) | +0.0 (OKX BTC-USDT) | +13.0 (Kraken PF_XBTUSD), +13.1 (Coinbase BTC-USD) | USDT |
| Lighter ETH (`0`) | +0.0 (OKX ETH-USDT) | +12.7 (Kraken), +13.1 (Coinbase) | USDT |
| Lighter SOL (`2`) | +0.4 (OKX SOL-USDT) | +11.5 (Kraken), +12.5 (Coinbase) | USDT |
| Lighter NVDA (`110`) | −11.7 (Aster NVDAUSDT) | | USD or USDC |
| Lighter WTI (`145`) | | +2.3 (dYdX WTI-USD) | USD or USDC |
| dYdX BTC-USD | −12.1 (OKX) | +0.9 (Coinbase), −1.4 vs Binance BTCUSDC | USD or USDC |
| Deribit BTC_USDC-PERPETUAL | −12.6 (OKX) | +0.5 (Coinbase), −1.8 vs Binance BTCUSDC | USD or USDC |
| Hyperliquid BTC (control) | +0.1 (OKX) | +13.1 (Kraken) | USDT |

Values are median basis-point differences of hourly median index prices.
101 Lighter crypto markets read within 4 bps of a USDT index and at least 9 bps
above USD, against a CEX USDT perpetual index, or against Aster's USDT and
Hyperliquid's native indexes where no CEX USDT perpetual was recorded.
BERA (`20`) is the 102nd, on the anchor test alone: it reads −0.6 against Hyperliquid
and −1.5 against Aster, while the OKX BERA index sits about 6 bps away from all three.

Not changed:

- Lighter stock, ETF, commodity and pre-IPO markets track USD or USDC (57 measured, e.g. gold
  +0.1 against Hyperliquid xyz:GOLD and −12.5 against Aster XAUUSDT), so they keep
  `usd-coin`.
- Lighter markets whose readings were noisy, between the two levels, or
  unmeasured keep `usd-coin` until checked: 130, 132, 157, 175, 176, 178, 179, 185,
  201, 203, 204, 211, 217, 219, 220, 221, 231, 232, 4095, 4096, 4097, and the
  unrecorded 51, 73, 74, 75, 80, 81, 89, 96, 97, 106, 107, 124, 125, 133, 152,
  169, 184, 213, 218, 222, 225, 230, 233.
- Deribit tracks USD or USDC. USDC traded about 2 bps below USD in this
  window, which is too close to separate from index noise. Deribit's BTC and ETH
  indexes read closer to USD and its alt indexes closer to USDC; that is a
  candidate for a later check, not a change.

## dYdX perpetuals track USD

dYdX's perpetuals now use `quote: usd`; their settlement stays USDC. This
rests on the chain's own oracle configuration, not on a measurement: its market map
(`/slinky/marketmap/v1/marketmap` on any dYdX v4 REST node, read 2026-10-30)
lists every one of its 248 tickers as `<BASE>/USD`, and each USDT-quoted source
carries `normalize_by_pair: USDT/USD`. BTC/USD, for example, reads Coinbase
BTC-USD and Kraken XXBTZUSD directly and Binance, Bybit, HTX, KuCoin, MEXC and
OKX BTC-USDT through USDT/USD. Every listed dYdX market's base is in that map.
