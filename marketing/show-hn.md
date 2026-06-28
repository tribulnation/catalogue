# Show HN Post

**Title:**
Show HN: Tribulnation Catalogue – open translation layer for crypto assets and networks

---

**Body:**

Every exchange invented its own names for everything.

| Exchange | Their string |
|---|---|
| Binance | `BSC` |
| MEXC | `BNB Smart Chain(BEP20)` |
| Bitget | `BEP20` |
| KuCoin | `BSC` |
| Bybit | `BSC (BEP20)` |
| Kraken | `BNB Chain` |

Same story with assets — Kraken calls Bitcoin `XXBT`, Hyperliquid calls it `197`.

Tribulnation Catalogue maps all of these to a single canonical record. Those external IDs also power the pricing SDK:

```python
from tribulnation.catalogue import Catalogue, MarketData

catalogue = Catalogue.load()
sdk = MarketData.new('usd', 'coingecko', 'twelvedata', 'alphavantage')

await sdk.current_price(catalogue.assets['bitcoin'])                  # → CoinGecko
await sdk.current_price(catalogue.assets['gold'])                     # → Twelve Data
await sdk.current_price(catalogue.assets['west-texas-intermediate'])  # → Alpha Vantage
```

Open dataset, MIT. Python and TypeScript clients, static JSON API (no auth, no rate limits).

GitHub: https://github.com/tribulnation/catalogue
Browse: https://catalogue.tribulnation.com
