# Kraken markets, earn and transfer identities — 2026-09-19

Adds four canonical earn assets, 23 native asset aliases, ten spot pairs, nine
perpetuals and 18 network aliases. Base: Catalogue `720d172`.

## Identity evidence

1. [Kraken's staking catalogue](https://www.kraken.com/features/staking) and
   [supported-asset table](https://support.kraken.com/articles/360000678446-cryptocurrencies-available-on-kraken)
   identify KAVA as Kava, FLOW as Flow, MINA as Mina Protocol and SCRT as Secret
   Network. These get separate native asset records. CoinGecko IDs were checked
   against the exact project names; no staking derivative is collapsed into ETH/SOL.
2. Nineteen aliases are witnessed by an exact native Futures instrument join to
   existing Catalogue records. The companion JSON preserves the instruments
   witnessing each mapping. This safely connects Futures' DOGE/XRP/USD spellings
   to the canonical assets already identified through Kraken's other namespaces.
3. Spot additions require live `online` status and the native AssetPairs fields.
   Perpetual selection follows the SDK's exact instrument/ticker filter: active,
   unsuspended, non-tradfi USD flexible perpetuals with unit contract size.
   Quote and settlement remain USD. No ticker-name prefix stripping is used.
4. Network additions use the precise plain names from retained WithdrawMethods
   observations and point only to existing blockchain platform objects. Examples:
   Lightning, Stellar, HyperEVM, Berachain, Filecoin and Internet Computer Protocol.

## Remaining work

All 73 retained earn rows now have asset translations. Complete withdrawal-row
resolution rises from 182 to 205 of 792; 521 observations still contain an unknown
asset identifier. All remaining asset and network IDs are in the companion JSON.

The current Catalogue lacks most of these projects. Native network names whose
platform objects are absent also stay unresolved. Asset Hubs are not the relay
chains. Bank rails are not represented as blockchain platforms.

Suffix-bearing routes such as `Ethereum (kBTC)`, `Ink (kHYPE)` and
`Arbitrum One (USDC.e)` need joint asset/network handling before they can safely
serve transfers. A global network alias would expose an asset misidentification:
for example, Kraken's source BTC identifier does not prove that its Ethereum
withdrawal delivers native BTC. Those routes remain unresolved.

SDK discovery still has 122 unmapped supported perpetual IDs. The spot inventory
has 869 unmapped IDs, including non-online products. Do not treat those as
resolved by a passing bounded consistency policy. Terminal integration and
replaying serving builds belong to the later integration task.

Related: [Catalogue #130](https://github.com/tribulnation/catalogue/issues/130).

## Coverage and validation

| Retained dataset | Rows | Resolved before | Resolved after |
| --- | ---: | ---: | ---: |
| earn_instruments | 73 | 62 | 73 |
| withdrawal_methods | 792 | 182 | 205 |

These checks use the latest retained local observations on September 19. Resolution
requires asset, optional yield/fee asset, and (for transfers) network translations.
No Terminal collection, database changes, serving replay or deduplication was performed.

The [companion JSON](kraken-coverage-2026-09-19.json) records accepted identities, public source URLs,
native market evidence where applicable, and remaining identifiers.

1. Full Catalogue validation passes with `PYTHONPATH=lib/src .venv/bin/python scripts/validate.py`.
2. Instrument URLs are generated with the repository script; `git diff --check` passes.
3. Fresh credential-free SDK discovery, construction and ticker reads pass for every added market with response validation enabled.

The SDK consistency run and its offline fingerprint/policy verifier both pass.
Check statuses: `{"deferred": 10, "pass": 1481}`. Explicit policy deferrals
are not resolved identities or exhaustive coverage. Reproduce from the SDK checkout:

```sh
.venv/bin/sdk-dev test consistency kraken --catalogue ../catalogue-kraken-followup/data --output /tmp/kraken-catalogue-review
.venv/bin/sdk-dev results verify /tmp/kraken-catalogue-review --catalogue ../catalogue-kraken-followup/data
```
