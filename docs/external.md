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
