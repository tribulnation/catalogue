# External IDs

External IDs are the provider-specific identifiers stored in `asset.external`.

## CoinGecko

Use the CoinGecko asset ID.

Example: `bitcoin`

Also supports currencies listed in https://docs.coingecko.com/reference/simple-supported-currencies, using the `currency:` prefix.

Example: `currency:gbp`

## CoinMarketCap

Use the CoinMarketCap numeric asset ID as a string.

Example: `1`

## Twelve Data

Use the Twelve Data symbol directly.

Examples: `XAU/USD`, `EUR/USD`, `AAPL`

Only add symbols that can be priced in USD. Forex pairs should be quoted against USD.

## Alpha Vantage

Alpha Vantage IDs are prefixed because the API uses different functions for different asset classes.

Only USD quotes are supported.

| ID | Query |
|---|---|
| `forex:USD` | no API call; return `1` |
| `forex:EUR` | `function=CURRENCY_EXCHANGE_RATE&from_currency=EUR&to_currency=USD` |
| `stock:TSLA` | `function=GLOBAL_QUOTE&symbol=TSLA` |
| `commodity:BRENT` | `function=BRENT&interval=daily` |

Historical forex uses `FX_DAILY` with `from_symbol=<currency>` and `to_symbol=USD`.

Stocks must be USD-listed symbols. Commodities must be Alpha Vantage commodity functions whose series is treated as USD-denominated.

## FRED

Use the FRED series ID directly when the series value is already USD per asset.

Examples: `DCOILWTICO`, `DCOILBRENTEU`, `DHHNGSP`, `DEXUSEU`

Use the `inverse:` prefix when FRED reports asset units per USD and the SDK should return USD per asset.

Examples: `inverse:DEXJPUS`, `inverse:DEXCAUS`, `inverse:DEXSZUS`

FRED is daily reference data, not real-time market data. Current pricing uses the latest published non-empty observation. Historical pricing returns exact-date observations only and does not forward-fill weekends or holidays.

## Checking IDs against the providers

`scripts/validate.py` runs offline, so it can only check that an external ID is
well-formed — not that it still points at the right asset. A provider can
delist an entry (the ID stops resolving) or rename one in place (the ID keeps
resolving, but to a different token), and neither shows up in validation.

`scripts/check_external_ids.py` resolves every CoinGecko and CoinMarketCap ID
against the provider and reports what it finds:

```sh
PYTHONPATH=lib/src .venv/bin/python scripts/check_external_ids.py
```

It needs network access, so it is run on demand rather than in CI.

- **unresolved** — the provider does not know the ID. Pricing for that asset
  fails outright. Find the current ID, or drop the mapping if the listing is
  gone.
- **mismatch** — the ID resolves, but to a token with a different symbol. This
  is the dangerous case: prices still come back, just for the wrong token.

A mismatch is never corrected automatically, because the benign and the broken
cases look identical from the outside. A rebrand keeps its provider ID, and the
catalogue deliberately uses short symbols where a provider spells out the full
deployment. Once a mismatch has been judged benign, record it in
`scripts/external_id_exceptions.json` with the reason:

```json
"wrapped-aave-gho:coingecko:wrapped-aave-ethereum-lido-gho": "Aave wrapper; CoinGecko spells out the chain in the symbol."
```

The key is `<asset>:<provider>:<external_id>`, so an acknowledgement covers one
exact mapping. Repointing the asset at a different ID makes the key stop
matching and the mismatch is reported again. `--all` lists the accepted ones
too; `--strict` makes unreviewed mismatches fail the run.
