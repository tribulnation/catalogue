# Aster market coverage — 2026-09-25

Extends the #184 Aster mappings to every currently trading spot market and
linear perpetual whose base, quote and settlement resolve to an **existing**
Catalogue asset. Adds 32 spot pairs, 422 perpetuals and 407 native symbol
translations. No asset, platform or icon is introduced. Base: Catalogue
`24e927fd`.

| Market | Discovered | Mapped before | Mapped after | Unmapped |
| --- | ---: | ---: | ---: | ---: |
| Spot | 71 | 3 | 35 | 36 |
| Perpetual | 584 | 17 | 439 | 145 |

## Selection and conventions

1. Discovery follows the SDK: spot `exchangeInfo` symbols with
   `status == 'TRADING'`; perpetuals with `status == 'TRADING'` and
   `contractType == 'PERPETUAL'`. `SETTLING` and `PENDING_TRADING` contracts
   are neither added nor delisted. Native IDs are Aster's `symbol`.
2. #184's conventions are kept: exchange `perp` / `spot`, settlement taken
   from `marginAsset`, and `1000X` contracts keep their native ID with
   `multiplier: 1000` and no wallet translation for the synthetic `1000X` name.
   Every added `1000X` multiplier was confirmed by price: Aster mark / 1000
   matches the base asset's reference price.
3. URLs come from `scripts/instrument_urls.py` (Aster Pro routes).
4. Translations are added for every mapped native base symbol, following
   #184 and the OKX/Deribit precedent for stock tickers.

## Quote and settlement assets

1. `USDT` maps to `tether`.
2. `USD1` maps to the existing `usd1` (World Liberty Financial USD1). Aster's
   spot `USD1` contract `0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d` equals the
   existing `bnb-chain` translation and CoinGecko `usd1-wlfi`. It covers 10 of
   15 USD1-margined perpetuals and 4 USD1-quoted spot pairs.
3. `U` maps to the existing `united-stables`. Aster's spot `U` contract
   `0xcE24439F2D9C6a2289F741120FE202248B666666` equals CoinGecko's
   `united-stables` deployment. Aster lists `U` as a `stable_coin` margin asset.
   Both U-margined perpetuals (`BTCU`, `ETHU`) are mapped.
4. `FORM` (Four) has no Catalogue record, so `CDLFORM` and `TESTFORM` are
   left unmapped.

## Identity evidence

1. **Perpetuals, cross-venue price.** For 330 new contracts, the only Catalogue
   candidate came from other venues' perpetual instruments or translations of
   the same symbol. It was accepted only when Aster's live mark price
   (÷ multiplier) was within 10% of every matching Binance, Bybit, OKX, Bitget
   or Hyperliquid mark and the candidate's CoinGecko price. Nearly all are
   within 1%. The ratios are in the JSON.
2. **Symbol-only alternatives rejected by price.** Where a ticker also matches
   a wrapper or an unrelated project, the price separates them: `DOT`, `TRX`,
   `ATOM`, `ETC`, `FIL`, `BCH`, `INJ`, `ZEC` and `ICP` resolve to the native
   coin, never to Binance-Peg or bridged wrappers. `STX` is Stacks, not
   Seagate; Seagate is Aster's `STXX`. `LIT` is Lighter, not Heima; Heima is
   Aster's `HEI`. `MET` is Meteora, `EDGE` edgeX, `ARC` AI Rig Complex, `VELO`
   Velo (not Velodrome), and `FRAX` the renamed governance token `frax-share`,
   as in the KuCoin report.
3. **CoinMarketCap-only assets.** Fourteen existing assets carry only a
   CoinMarketCap ID: KNC, OGN, ARPA, NEIRO, BLESS, BLUAI, APR, US, POLYX, INX,
   PROMPT, PRL, AVAAI and PROS. Each Aster mark is within 0.6% of CMC's price
   for that exact ID. `APR` is aPriori, which CMC now labels Capricorn,
   consistent with the asset's own description.
4. **Stocks, ETFs and commodities.** These map only to existing `stock`,
   `fund` and `commodity` records, never to xStock, rToken or bStock wrappers.
   Aster's `tags` and name identify the issuer. Its mark matches the Yahoo
   price of the asset's own `external.yahoo` symbol within 0.5%, except gold and silver (below). This covers
   68 contracts, including USD1-margined `METAUSD1`, `MUUSD1`, `SNDKUSD1`,
   `SPCXUSD1`, `GPROUSD1`, `CLUSD1` and `XAUUSD1`.
   `CL`, `BZ` and `NATGAS` track front-month futures and map to
   `west-texas-intermediate`, `brent` and `natural-gas`, as Hyperliquid
   `xyz:CL`, Deribit `BRENTOIL` and OKX `NG` already do. Gold and silver
   perpetuals trade 0.6–0.75% below December futures, consistent with spot
   pricing; venue perpetuals of both match within 0.1%.
5. **Spot, by contract.** Aster publishes `baseAssetAddress`. Each of 28 spot
   bases was accepted only when that exact address is a CoinGecko deployment of
   the coin ID in the Catalogue asset's `external`, or a CMC deployment of the
   asset's CMC ID for BLESS and US (Talus). Many pairs are illiquid, with last
   trades up to 30 days old, so last price is recorded but not used as identity
   evidence. `BNB`, `SOL` and `USDC`
   publish no address and are the native coins, matching liquid prices within
   0.05%. `BIO` also publishes no address. Its book mid is within 0.1% of
   the reference price, and the same symbol's perpetual is independently
   price-verified.
6. **VERONA** is XION after a 1:1 ticker rename with no contract migration
   ([Verona docs](https://docs.verona.dev/en/others/rebrand-from-xion),
   [Bybit notice](https://announcements.bybit.com/en/article/xion-xion-token-swap-and-rebrand-to-verona-verona--blt93a96e2fa6e35b9e/)).
   Aster's VERONA contract equals CoinGecko `xion-2`, so `VERONA` maps to the
   existing `xion`.

## Deliberate exclusions

1. **Pre-launch** (5): `OPENAIUSDT`, `ANTHROPICUSDT`, `POLYMARKETUSD1`,
   `MOONSHOTUSD1`, `OURAUSD1`. Aster marks them `pre-launch`; they have no
   tradable underlying.
2. **Index** (1): `BTCDOMUSDT`.
3. **Ticker collisions** (5 perp, 1 spot):
   1. `MEME` prices at about 45× Catalogue `memecoin` and other venues' MEME.
   2. `TST` is the BNB Chain "Test" token (CoinGecko `test-3`), not Catalogue
      TeleSwap.
   3. `UP` is Unitas, not Superform.
   4. `EWT` is the iShares MSCI Taiwan ETF, not Energy Web.
   5. `BNCUSD1` is a USD1-RWA stock contract, not Bifrost.
4. **Different listing** (2): `SKHYNIXUSDT` and `SKHYNIXUSD1` track Korea
   Exchange shares. Catalogue only has the ADR, which Aster's `SKHYUSDT` maps
   to.
5. **Internal test** (5 spot): `TESTUSDT`, `TESTUSD1`, `TESTFORM`,
   `TEST1USDT`, `TEST2USDT`.
6. **No existing asset** (77 perp crypto, 55 perp traditional, 29 spot).
   These include Hong Kong and Korean equities, several US equities and ETFs,
   copper/platinum/palladium, bStock tokens (`SPCXB`, `SKHYB`), and many BNB
   Chain launches. Adding assets was out of scope by owner decision.

The companion JSON lists every unmapped ID with its category and reason.

## Open questions

1. Aster spot `BTC` and `ETH` publish BNB Chain addresses of BTCB
   (`binance-bitcoin`) and Binance-Peg ETH (`binance-peg-ethereum`). #184
   maps those spot bases and the `BTC`/`ETH` translations to `bitcoin` and
   `ethereum`. That is unchanged here and needs an owner decision, because the
   same symbols also denote perpetual underlyings and margin assets.
2. Bybit and KuCoin translate `TST` to `teleswap-token`. Their TST markets may
   be the same BNB Chain Test token as Aster's. This was not investigated or
   changed.

## Validation

1. `PYTHONPATH=lib/src .venv/bin/python scripts/validate.py` passes.
2. `scripts/check_new_assets.py --base origin/main` passes with zero new
   assets.
3. The scripts unit tests pass (16 tests), and `git diff --check` passes.
4. URLs were generated with the repository script: 32 spot and 422 perpetual.
5. The SDK consistency run and its offline verifier both pass. Check
   statuses: `{"pass": 968, "excluded": 3}`, where the exclusions are the
   unsupported `perp_stats` suites. All 474 mapped markets pass
   `catalogue_coverage` and `catalogue_identity`.

   The SDK `.venv` pins an older `tribulnation-catalogue` that rejects current
   blockchain categories (`cosmos-sdk`), so the run loads this worktree's
   library. Reproduce from the SDK checkout:

```sh
PYTHONPATH=../catalogue-aster-coverage/lib/src .venv/bin/sdk-dev test consistency aster --catalogue ../catalogue-aster-coverage/data --output /tmp/aster-catalogue-review
PYTHONPATH=../catalogue-aster-coverage/lib/src .venv/bin/sdk-dev results verify /tmp/aster-catalogue-review --catalogue ../catalogue-aster-coverage/data
```

The [companion JSON](aster-coverage-2026-09-25.json) records sources and
snapshot hashes, each added market's method and evidence, the translations
added, and every remaining unmapped ID.
