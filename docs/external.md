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
