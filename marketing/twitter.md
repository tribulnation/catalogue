# Twitter / X Thread

---

**Tweet 1 (hook):**

Every exchange has a different name for the same blockchain network.

Here's what they call Avalanche C-Chain:

- MEXC: `AVAX_CCHAIN`
- Bitget: `AVAXC-Chain`
- Binance: `AVAX`
- Kraken: `Avalanche C-Chain`
- Hyperliquid calls Bitcoin `197`

We built Tribulnation Catalogue — the translation layer. 🧵

---

**Tweet 2 (the problem):**

If you've ever built a multi-exchange integration, portfolio tracker, or on-chain reconciliation tool — you've hit this.

Binance withdrawal says `BSC`. MEXC says `BNB Smart Chain(BEP20)`. Bitget says `BEP20`. All the same chain.

Matching these by hand doesn't scale.

---

**Tweet 3 (the solution):**

Tribulnation Catalogue is an open, typed dataset that resolves this.

Feed it any exchange's raw asset or network string → get back a canonical record: ID, display name, symbol, icon, peg info, external IDs.

Python + TypeScript clients. Static JSON API. No auth, no rate limits.

---

**Tweet 4 (breadth):**

It covers:

→ Assets (crypto, forex, commodities, stablecoins, wrapped tokens)
→ Platforms (CEX, DEX, blockchains)
→ Instruments (spot pairs, perpetuals, pools — mapped to canonical IDs)
→ Network translations per exchange
→ Asset translations per exchange
→ Icons (square, maskable SVGs)

---

**Tweet 5 (pricing):**

There's also a `MarketData` SDK.

It uses the catalogue's external IDs to route price requests to the right provider automatically — CoinGecko for crypto, Twelve Data for gold, Alpha Vantage for oil.

```python
sdk = MarketData.new('usd', 'coingecko', 'twelvedata', 'alphavantage')
price = await sdk.current_price(catalogue.assets['gold'])  # → Twelve Data
```

---

**Tweet 6 (CTA):**

Open source (MIT).

GitHub: https://github.com/tribulnation/catalogue
Browse the catalogue: https://catalogue.tribulnation.com
PyPI: tribulnation-catalogue
npm: @tribulnation/catalogue

If you're building anything multi-exchange, give it a look.

---

## Standalone tweet (shorter version for organic posting)

Every exchange calls the same blockchain something different.

Binance: `BSC`
MEXC: `BNB Smart Chain(BEP20)`
Bitget: `BEP20`
Bybit: `BSC (BEP20)`
Kraken: `BNB Chain`

Tribulnation Catalogue maps all of them to `bnb-chain` — open source, typed, with icons and pricing.

https://github.com/tribulnation/catalogue
