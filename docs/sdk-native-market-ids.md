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
without inventing new asset identities. dYdX settles and charges fees in
USDC, while retaining native `*-USD` market names; its perpetual `quote` is USD
(see below). No global USD-to-USDC mapping is introduced.

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
- dYdX and Deribit track USD or USDC. USDC traded about 2 bps below USD in this
  window, which is too close to separate from index noise. dYdX was later settled
  from its protocol definition instead (next section). Deribit's BTC and ETH
  indexes read closer to USD and its alt indexes closer to USDC; that is a
  candidate for a later check, not a change.

## dYdX perpetuals track USD

dYdX v4 perpetuals carry `quote: usd`, `settlement: usd-coin`. Recorded prices
cannot separate USD from USDC (above), but the protocol defines the target:

- Every oracle market is a `<BASE>/USD` currency pair. All 248 entries of the
  mainnet market map (`/slinky/marketmap/v1/marketmap`) and all 297 market
  params (`/dydxprotocol/prices/params/market`) are quoted in `USD`; there is no
  USDC-quoted oracle market, and the `USDC/USD` ticker is disabled.
- USDT-quoted sources are converted to USD: their provider configs carry
  `normalize_by_pair: USDT/USD` (legacy `adjustByMarket: "USDT-USD"`,
  `BTC-USD = BTC-USDT * USDT-USD`), and the oracle multiplies each such price
  by its own `USDT/USD` index price. USD sources (Coinbase, Kraken, Crypto.com,
  Bitstamp) are used as is. `USDT/USD` itself is a median of Coinbase
  `USDT-USD`, Kraken `USDTZUSD`, inverted `USDC/USDT` books, and two crosses
  through `BTC/USD` and `ETH/USD`.
- USDC collateral counts one-for-one as quote quantums, and 10^6 quote quantums
  are defined as 1 USD, so the protocol values 1 USDC at exactly 1 USD.

The index therefore tracks USD; positions settle in USDC that the protocol
holds at par. This mirrors Hyperliquid's `quote: tether`,
`settlement: usd-coin`, with the index currency USD instead of USDT.

## Pacifica crypto perpetuals track USDT

Pacifica's crypto perpetuals carry `quote: tether`; `settlement` stays
`usd-coin`. Pacifica's [Oracle Price & Mark Price](https://docs.pacifica.fi/trading-on-pacifica/contract-specifications/oracle-price-and-mark-price)
page says the oracle price "is calculated as a weighted average of USDT
denominated prices from major exchanges" (Binance 2, OKX 1, Bybit 1,
Hyperliquid 1), and the oracle price is the index used for funding.

Measured over 60 rounds on 2026-10-30, 17:30 to 17:48 UTC (USDT 11.7 bps below
USD), Pacifica's crypto oracle prices read a median −1.0 bps against Binance
USDT-M indexes and +14.1 bps against Kraken USD spot. 53 markets change: the
crypto markets and `PAXG`, which trades as `PAXGUSDT` on the same venues.

Not changed: the 23 stock, fund, commodity and FX markets. The page above names
only crypto venues, and their readings split. CRCL, HOOD, NVDA, PLTR, SPCX,
TSLA, XAU, XAG and PLATINUM read 0.0 to +2.8 bps against Ostium's USD feeds,
which is USD or USDC; META, MSTR, MU, SNDK and DRAM read +9.3 to +10.1 bps, which
is near the USDT level. Neither is backed by a published definition, so they
keep `usd-coin`.
