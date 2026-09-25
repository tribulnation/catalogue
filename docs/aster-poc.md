# Aster identifier coverage

> Mainnet market coverage has since been extended to every trading spot pair and
> linear perpetual that resolves to an existing asset (35 spot, 439 perpetuals).
> See [the 2026-09-25 coverage report](reports/aster-coverage-2026-09-25.md) for
> current counts and the remaining unmapped IDs. The notes below record the
> original testnet PoC pass (#184).

The SDK Aster PoCs were exercised on testnet on 2026-09-25. The added Catalogue
records cover the identifiable subset of those native IDs, cross-checked with
validated `typed-aster==0.1.0` mainnet exchange-information responses.

1. `data/asset_translations/aster.json` adds 16 native symbols mapped to existing
   assets. No asset or platform record is introduced.
2. `data/instruments/perpetual/aster.json` adds the 17 active testnet perpetuals
   also present on mainnet, under exchange `perp`. Native `1000PEPEUSDT` and
   `1000SHIBUSDT` retain their IDs and represent `pepe`/`shiba-inu` with multiplier
   1000. The synthetic base names are not 1:1 wallet-asset translations.
3. `data/instruments/spot/aster.json` adds `ASTERUSDT`, `BTCUSDT` and `ETHUSDT`,
   under exchange `spot`.
4. `scripts/instrument_urls.py` generates the native Pro trading URLs. The
   official app route is `/en/trade/pro/{spot|futures}/{symbol}`; the legacy
   `/en/futures/` route currently redirects BTC to the separate 1001x interface.

Sources:

1. [Official futures exchange-information contract](https://asterdex.github.io/aster-api-website/futures-v3/market-data/#exchange-information)
   and [live mainnet response](https://fapi.asterdex.com/fapi/v3/exchangeInfo).
2. [Official spot exchange-information contract](https://asterdex.github.io/aster-api-website/spot-v3/market-data/#trading-specification-information)
   and [live mainnet response](https://sapi.asterdex.com/api/v3/exchangeInfo).
3. [Official Pro spot page](https://www.asterdex.com/en/trade/pro/spot/BTCUSDT)
   and [Pro futures page](https://www.asterdex.com/en/trade/pro/futures/BTCUSDT).
4. [Official internal-test-symbol notice](https://asterdex.github.io/aster-api-website/spot-v3/general-info/).

Remaining gaps are deliberate: `TEST`/`TESTUSDT` is an internal-test symbol, and
`EVENT4_ALGERIA_WIN_Y`/`EVENT4_ALGERIA_WIN_N` and their USDT pairs are testnet
outcome tokens whose identities are not established in this catalogue. They
remain visible in the PoC's gap output. No synthetic canonical assets were added
to make that diff empty.

Validation: `PYTHONPATH=lib/src .venv/bin/python scripts/validate.py` passes, and
the SDK's `sdk-dev catalogue check` accepts Aster's symbol identifier form.
