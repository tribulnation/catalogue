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
  +0.1 against Hyperliquid xyz:GOLD and −12.5 against Aster XAUUSDT). Lighter's
  published oracle sources later settled most of them as USD (see "Lighter
  index sources").
- Lighter markets whose readings were noisy, between the two levels, or
  unmeasured were left for a later check: 130, 132, 157, 175, 176, 178, 179, 185,
  201, 203, 204, 211, 217, 219, 220, 221, 231, 232, 4095, 4096, 4097, and the
  unrecorded 51, 73, 74, 75, 80, 81, 89, 96, 97, 106, 107, 124, 125, 133, 152,
  169, 184, 213, 218, 222, 225, 230, 233. The same section resolves most of them.
- dYdX and Deribit track USD or USDC. USDC traded about 2 bps below USD in this
  window, which is too close to separate from index noise. dYdX was later settled
  from its protocol definition instead (next section). Deribit's BTC and ETH
  indexes read closer to USD and its alt indexes closer to USDC; Deribit's own
  index definitions later confirmed both (see "Deribit linear perpetuals").

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

## GMX perpetuals track USD

GMX v2 perpetuals carry `quote: usd`; `settlement` stays `usd-coin`. Checked
2026-10-30 from the protocol itself:

- GMX prices every token, including the collateral stablecoins, in USD. The
  oracle stores a token's USD price scaled by 10^30 (gmx-synthetics `README.md`,
  "Oracle prices"), and the keeper API
  (`https://arbitrum-api.gmxinfra.io/prices/tickers`) quoted USDC at 0.99976 and
  USDT at 0.99890 on 2026-10-30 17:23 UTC. USDC is a priced token like any other,
  not the unit of account.
- The signed prices are Chainlink Data Streams reports (`oracleType:
  realtimeFeed2` in `/signed_prices/latest`), whose feeds are `<BASE>/USD`.

Index positions are therefore valued in USD; profits are paid out in the
market's collateral token at its own oracle price. All 100 GMX markets
(`<BASE>/USD`) change.

## Ostium perpetuals track USD

Ostium perpetuals carry `quote: usd` (or the foreign currency for its `USD-*`
FX pairs, unchanged); `settlement` stays `usd-coin`. Checked 2026-10-30:

- Ostium's price publisher (`https://metadata-backend.ostium.io/PricePublish/latest-prices`)
  defines every feed as a `from`/`to` pair. All 70 catalogued `<BASE>-USD`
  markets have `to: USD`, including `EUR-USD` and `GBP-USD`, which are the
  EUR/USD and GBP/USD exchange rates, not a stablecoin rate. No feed is quoted
  in USDC or USDT.
- Of the publisher's 94 feeds, 85 are quoted in `USD`; the rest are `USD-<CCY>`
  FX pairs and local-currency indices (`DAX-EUR`, `NIK-JPY`, ...).

USDC collateral pays the USD PnL one-for-one. The five `USD-<CCY>` markets
(`USD-JPY`, `USD-CAD`, `USD-CHF`, `USD-HKD`, `USD-MXN`) already had base `usd`
and their foreign currency as quote, and are unchanged.

## Derive perpetuals track USD

Derive perpetuals carry `quote: usd`; `settlement` stays `usd-coin`. Checked
2026-10-30 against the Derive v3 API (`POST https://api.derive.xyz/v3/public/get_instrument`):

- Every one of the 15 catalogued perpetuals reports `perp_details.index:
  "<BASE>-USD"` (e.g. `BTC-PERP` → `BTC-USD`) next to `quote_currency: "USDC"`,
  the cash asset it margins and settles in.
- The spot feeds behind those indexes are USD-denominated: `public/get_currency`
  priced USDC itself at 0.99997 and USDT at 0.99889, so USDC is a priced asset,
  not the unit.

## Paradex perpetuals track USD

Paradex perpetuals carry `quote: usd`; `settlement` stays `usd-coin`. Checked
2026-10-30 against `https://api.prod.paradex.trade/v1/markets`:

- All 66 live perpetuals (`<BASE>-USD-PERP`) report `quote_currency: "USD"`
  and `settlement_currency: "USDC"`, each with its own oracle `price_feed_id`.
- USDC has its own mark price (`/v1/markets/summary?market=USDC`: 0.99978 on
  2026-10-30), so the index unit is USD and USDC collateral is valued against it.

## Bluefin perpetuals track USD

Bluefin perpetuals carry `quote: usd`; `settlement` stays `usd-coin`. Bluefin's
[Oracle and Index Price](https://learn.bluefin.io/bluefin/bluefin-perps-exchange/trading/oracle-and-index-price)
page says both feeds "retrieve the USD value of perpetual contracts", and that on
Bluefin v2 (Sui) the oracle and index prices are received from the Pyth network,
whose feeds are `<BASE>/USD`. USDC is the only margin asset
(`/v1/exchange/info`, weight 1). All 8 markets change.

## Deribit linear perpetuals

Deribit's `BTC_USDC-PERPETUAL` and `ETH_USDC-PERPETUAL` carry `quote: usd`; the
other 139 linear perpetuals keep `quote: usd-coin`. All settle in USDC. Checked
2026-10-30:

- Each perpetual names its index in `public/get_instruments` (`price_index`):
  `btc_usdc`, `eth_usdc`, `sol_usdc`, `aapl_usdc`, and so on. Deribit publishes
  separate `<base>_usd`, `<base>_usdc` and `<base>_usdt` indexes
  (`public/get_index_price_names`).
- BTC and ETH: the [Linear Perpetual](https://support.deribit.com/hc/en-us/articles/31424969384605)
  specification says that since 15 July 2025 "the BTC-USDC index is pegged to
  the BTC-USD index, and the ETH-USDC index is pegged to the ETH-USD index",
  with USD/USDC parity assumed for settlement. `public/get_index_price` returned
  identical `btc_usd` and `btc_usdc` (77,088.23) and `eth_usd` and `eth_usdc`
  (2,240.05) values while `usdc_usd` was 0.9998.
- Everything else: crypto perpetuals use a Deribit `<BASE>-USDC` index or an
  `<BASE>-USD` Coinbase index, and the
  [RWA Perpetual](https://support.deribit.com/hc/en-us/articles/38325634622493)
  specification says the USDC contract "is adjusted from that USD index using
  the USDC-USD rate". Their `_usdc` indexes are not pegged: `aave_usdc`,
  `link_usdc` and `hype_usdc` sat 2 to 3 bps above their `_usd` twins, the
  USD/USDC rate at the time, which fits a USDC index. The RWA specification
  covers only the RWA contracts, and a 2 to 3 bps gap is too small to tell USD
  from USDC on its own, so for the crypto alts `usd-coin` is consistent with
  the evidence rather than confirmed; the label is unchanged.

The inverse `BTC-PERPETUAL` and `ETH-PERPETUAL` (`btc_usd`, `eth_usd`, settled in
BTC and ETH) are not catalogued.

## Lighter index sources

Lighter publishes the sources behind every market's index price at
`GET https://mainnet.zklighter.elliot.ai/api/v1/priceOracleInfo`
([API reference](https://docs.lighter.xyz/api/info/priceoracleinfo)): the
`source` in use and the `median_sources` it takes the median of. A source names
its currency: `pythlazer / usdt`, `stork / usdt`, `chainlink / usdt` and
`uniswap * eth / usdt` are USD or ETH prices divided by USDT, `binance`, `okx` and
`mexc` are those venues' USDT pairs, while plain `pythlazer` and `redstone` are,
by our inference, the oracles' own `<BASE>/USD` feeds: Lighter's API reference
does not define the currency of an unsuffixed source, but Pyth Lazer's equity,
metal and FX feeds are USD, and these markets read −0.3 bps against Ostium's
USD feeds. No market mixes suffixed and unsuffixed sources. Read on 2026-10-30 at 17:31 UTC:

- 69 markets take the median of plain `pythlazer` or `redstone` alone: metals,
  FX (`EURUSD`, `GBPUSD`, `AUDUSD`, `NZDUSD`), US stocks and ETFs, indices, `WTI`,
  `NATGAS` and `XCU`. They move from `usd-coin` to `quote: usd`: 92, 93, 96, 97,
  106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 121, 122, 123, 128,
  129, 136, 137, 138, 139, 145, 146, 147, 151, 152, 153, 156, 158, 164, 165, 166,
  167, 168, 174, 175, 176, 177, 178, 179, 185, 186, 187, 188, 189, 191, 194, 195,
  196, 197, 206, 207, 208, 209, 210, 211, 214, 216, 218, 222, 223, 224, 226, 228,
  229.
- 16 crypto markets labelled `usd-coin` take only USDT-denominated sources and
  move to `quote: tether`, like Lighter's other crypto markets: 34, 73, 74, 81,
  125, 130, 132, 157, 184, 213, 219, 221, 231, 232, 233, 4095.
- The 103 markets already on `tether` all take USDT-denominated sources, and the
  five `USD<CCY>` FX markets (98, 99, 100, 105, 198) take plain `pythlazer`, as
  their foreign-currency quote assumes. Neither changes.

Not changed, because the source does not name a currency:

- `internal_price` (Lighter's order-book EMA while the external feed is stale,
  e.g. Asian stocks out of hours, pre-IPO markets): 160, 161, 162, 192, 193, 199,
  201, 202, 203, 205, 217, 220, 230, 4096, 5628.
- `rolling` futures pricing: 159 (`BRENTOIL`); a median with no listed source:
  204, 225; plain `uniswap`: 4097.
- Markets missing from `priceOracleInfo` (inactive or renamed): 22, 28, 51, 70,
  75, 80, 89, 124, 133, 169.

These keep `usd-coin` until their sources are readable.
