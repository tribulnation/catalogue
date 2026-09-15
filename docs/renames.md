# Renames and ticker reuse

When a project renames its token, a venue's ticker can end up meaning something
different than it used to. This is the single most dangerous kind of catalogue
error, because nothing breaks: prices keep arriving, they are just prices for
the wrong asset.

## What the catalogue records

An instrument records **what the market trades today**. There is no date field
on `Spot` or `Perpetual`, and this document does not add one.

That is sufficient because of how venues actually handle renames: a venue
almost always **opens a new market** rather than repointing an existing one. The
old ticker is halted and delisted, the new ticker starts with an empty chart. So
the new ticker's history is unambiguous all the way back to its first candle,
and one mapping describes it completely.

The case that would genuinely need a date is **ticker reuse** — the same symbol
on the same venue meaning asset A before some date and asset B after. Treat that
as unrepresentable today: do not map it to whichever asset is current and hope
for the best. Raise it, because it needs a schema change rather than a data fix.

## Telling the two apart

Do not assume. The question is empirical, and it is answered by asking the venue
when the market's history starts:

```sh
# Binance: first monthly candle for the ticker
curl -s 'https://data-api.binance.vision/api/v3/klines?symbol=FRAXUSDT&interval=1M&startTime=0&limit=1'
```

- History begins **at or after the rename** → new market, no boundary, one
  mapping is correct and complete.
- History **predates the rename** → the ticker was reused. Stop and escalate.

Check the old ticker too. If it still exists in a halted state (Binance reports
`status: "BREAK"`), that is direct confirmation the venue replaced rather than
repointed it.

## Worked example: Frax, January 2026

Frax renamed its governance token FXS to FRAX, which collided with the symbol of
the protocol's own legacy stablecoin. The catalogue mapped every venue `FRAX`
market to `frax` (Legacy Frax Dollar), so a $0.26 governance token was priced as
a $0.99 stablecoin.

The evidence:

| | |
|---|---|
| Binance `FRAXUSDT` first candle | 2026-01, matching the rename |
| Binance `FXSUSDT` first candle | 2021-12, status now `BREAK` |
| KuCoin `FRAX-USDT` first candle | 2026-02 |
| Observed price | ~$0.26 on Binance, Bybit and KuCoin |
| `frax` (Legacy Frax Dollar) | ~$0.99 |

So the `FRAX` ticker is **new on every venue** and has only ever meant the
governance token. There is no historical boundary to represent: the mapping was
simply wrong from the day the market opened, and correcting it corrects the
whole history too.

The two identities stay separate assets, as they are separate credits:

- `frax` — Legacy Frax Dollar, the stablecoin. Keeps its own external IDs
  (CoinGecko `frax`, CoinMarketCap `6952`), its on-chain address and its
  holdings. Untouched by the rename.
- `frax-share` — the governance token, symbol now `FRAX`. Its own external IDs
  (CoinGecko `frax-share`, CoinMarketCap `6953`) and its own addresses.

Note that the ERC-20 still reports `FXS` on-chain. A rename is a branding and
venue-listing event; it does not redeploy the contract. Symbol matching against
chain data and symbol matching against venue data can therefore disagree, and
both can be right.

## Why symbol matching caused this

The mapping was wrong because `FRAX` was matched by symbol, and two different
assets legitimately carry that symbol. Duplicate symbols are normal here — the
catalogue has a number of them — so a symbol is never sufficient evidence of
identity on its own. Confirm against price, the provider's own record, or the
contract before mapping.

`scripts/check_external_ids.py` catches the provider-side half of this
automatically; see [external.md](external.md).
