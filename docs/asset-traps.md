# Known asset traps

Cases where the obvious route produces a **wrong price or a double-counted
balance**, recorded so they are not rediscovered the hard way. The general rules
live in [AGENTS.md](../AGENTS.md); this is the list of things that have actually
bitten, and how each was resolved.

Every claim below was read back from the chain or the provider, not taken from a
feed.

## Three JPYC contracts, all reporting `JPYC`

Symbol matching cannot separate these — all three return `JPYC` and 18 decimals,
and all three have real bytecode:

| | Address | What it is |
|---|---|---|
| ❌ | `0x431D5dfF03120AFA4bDf332c61A6e1766eF37BDB` | legacy prepaid v2, CoinGecko `jpy-coin` |
| ❌ | `0x6AE7Dfc73E0dDE2aa99ac063DcF7e8A63265108c` | legacy prepaid v1 (Polygon PoS child) |
| ✅ | `0xE7C3D8C9a439feDe00D2600032D5dB0Be71C3c29` | the regulated JPYC, CoinGecko `jpycoin` |

The legacy contracts are a discontinued prepaid instrument (自家型前払式支払手段)
with **no cash redemption right**, so nothing arbitrages their price back to the
yen. They trade on dust liquidity at a large fictitious premium — measured at
**+44.8%** against the yen reference ($0.00934 vs $0.00645) — while the
regulated token sits within 0.14% of it.

Only `0xE7C3…` is mapped, as `jpyc`. It is the same address on Ethereum,
Polygon, Avalanche and Kaia, and is issued by JPYC Inc. as a registered Funds
Transfer Service Provider with a statutory redemption obligation.

## Monerium EURe: two addresses, one balance ledger

On every chain Monerium has a V1 front-end contract and a V2 proxy. They are
**not two assets** — they share one ledger:

```
V1.getController() -> the V2 proxy address
V1.totalSupply()   == V2.totalSupply()
```

Verified on both Gnosis (`0xcB444e90…` → `0x420CA0f9…`) and Ethereum
(`0x3231Cb76…` → `0x39b8b638…`). A holder's balance reads identically from
either, so **mapping both would double-count the same euro**.

Only the V2 address is mapped, on Ethereum, Gnosis, Polygon, Arbitrum, Linea and
Scroll. CoinGecko carries both as separate coins at the same price —
`monerium-eur-money-2` is the active listing, `monerium-eur-money` is marked
`[OLD]`. Use the former.

The one thing the V1 address is still needed for is indexing: each contract
emits its own `Transfer` events, so watching only V2 undercounts activity.
That is an indexer concern, not a balance concern.

## bCSPX is a debt security, not a share

`backed-cspx` is a **tokenised tracker certificate** issued by Backed Assets
(JE) Limited in Jersey. Holders have creditors' rights against the issuer, not
ownership of iShares Core S&P 500 UCITS ETF shares. It **floats** with the ETF
rather than holding a peg, and the ETF is accumulating, so there are no
distributions. Kraken's parent Payward acquired Backed Finance AG in January
2026, and the original bTokens are no longer in the issuer's continued public
offer — S&P 500 exposure going forward is SPYx.

For pricing, use the aggregate: CoinGecko's $820.28 tracks `CSPX.L` at $818.15,
within 0.26%. Do **not** read GeckoTerminal's Gnosis pool, which sits ~23% below
NAV on about $0.18 of daily volume.

## Status changes worth knowing

- **USDM (Mountain Protocol) is wound down.** Primary market closed August 2025,
  reward rate 0%, backing moved to a Uniswap pool — exiting is a swap at market,
  not a redemption claim. Still near $1, so pricing is unaffected, but it is no
  longer yield-bearing. Market cap is down to about $1.4M.
- **`USDM`/`USDm` is a severe symbol collision** — at least five unrelated
  assets use it (MegaUSD, Mento Dollar, Moneta, Monetrix, Mountain). The
  catalogue already carries two, `mountain-protocol-usd` and `mento-dollar`.
  Symbol matching will pick the wrong one.
- **cUSD was renamed in place.** `0x765DE816845861e75A25fCA122bb6898B8B1282a`
  now returns `Mento Dollar`/`USDm`. Same contract, no migration; CoinGecko kept
  the id `celo-dollar`. Catalogued as `mento-dollar`.
- **axlUSDC is NOT wound down**, contrary to a common assumption — live mints
  and burns on Base and Avalanche, `deprecated: null` in Axelar's own registry.
  But the obligor is **Axelar's validator set, not Circle**, so it would need
  its own asset rather than folding into `usd-coin`. Not catalogued yet.
- **PAR (Mimo/Parallel) is legacy**, superseded by USDp in Parallel V3, with
  roughly $3.4k of Polygon liquidity. Not catalogued, and not worth adding at
  that depth.

## Tooling notes

- **A dead RPC looks exactly like "no contract here."** `polygon-rpc.com`
  returns "API key disabled" and yields empty results that are indistinguishable
  from an address with no code. Use `polygon-bor-rpc.publicnode.com`. This bit
  again during this pass: `rpc.ankr.com/eth` reported `has_code: false` for a
  contract that `ethereum-rpc.publicnode.com` reads fine. **Confirm a negative
  against a second RPC before concluding an address is empty.**
- Blockscout's `api/v2/addresses/<addr>` **verified contract name** is the
  single most useful signal: `UChildERC20Proxy` means Polygon PoS bridge,
  `AnyswapV5ERC20` means a dead Multichain wrapper, `BurnableMintableCappedERC20`
  means an Axelar gateway.
- `jpyc.co.jp` returns 403 to non-browser user agents. Several issuer sites are
  JS SPAs whose authoritative address lists live in `llms.txt`, `sitemap.xml` or
  the site's own JS bundle.
- Axelar's docs warn that **`satellite.money` is no longer controlled by
  Axelar** and still serves a live site. Never link it.
- Venue APIs are not uniformly reachable. Binance and Bybit geo-block some
  hosts; `data-api.binance.vision` serves spot data where `api.binance.com` does
  not, and CoinGecko's `/exchanges/<id>/tickers` and
  `/derivatives/exchanges/<id>` endpoints are a usable second source when a
  venue is unreachable. Treat them as corroboration, not as the venue's own word
  — they carry stale rows (a renamed MEXC `TON_USDT` was still listed there
  after MEXC itself returned "Contract not exists").

## Kraken symbol and name collisions

Kraken's [official asset table](https://support.kraken.com/articles/360000678446-cryptocurrencies-available-on-kraken)
uses `MET` for Meteora, `OMNI` for Omni and `VELO` for Velo. Those symbols must not
be mapped to the Catalogue's Metronome, OmniCat or Velodrome Finance records.

`MIM` is an even closer collision: Kraken lists Magic Internet Money on Bitcoin,
while `magic-internet-money` in Catalogue is Abracadabra's USD stablecoin. A
2026-09-19 live `MIMUSD` ticker returned `0.0005371000 USD`, corroborating the
mismatch. Matching both name and symbol is insufficient here. Leave these native
IDs untranslated until the actual project has its own verified Catalogue identity.

The [Kraken Spot qualification report](reports/kraken-spot-2026-09-19.md) records
the verified additions and remaining gaps.
