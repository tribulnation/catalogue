# Kraken Spot aliases and active pairs — 2026-09-19

This pass extends the native `ZUSD` → `usd` fix with verified aliases for existing
Catalogue assets and active Kraken Spot instruments. It creates no new canonical
assets and does not change existing instrument identities or perpetual mappings.

## Coverage

| Measure | Before this PR | After |
| --- | ---: | ---: |
| Native asset translations in Kraken's file | 41 | 201 |
| Missing native asset IDs used by live Spot pairs | 634 | 474 |
| Mapped live Spot pairs | 536 | 571 |
| Missing live Spot pairs | 914 | 879 |
| Missing pairs with status `online` | 823 | 788 |

Kraken's validated metadata listed 1,450 Spot pairs and 673 distinct base/quote
asset IDs. The remaining missing pairs include 80 `cancel_only` and 11 `post_only`
listings. Those statuses are not treated as delistings, but this pass only adds
pairs whose metadata reports `online`. The 131 missing perpetual instruments from
the SDK qualification remain a separate follow-up.

## Identity evidence

1. `ZUSD` resolves to USD through Kraken Assets (`altname = USD`).
2. Another 142 native aliases come from exact live `AssetPairs.base`/`quote` fields
   joined by market altname to existing Kraken Catalogue instruments. Every witness
   for a native asset agreed on one existing canonical identity. Existing explicit
   translations were checked for conflicts; none were found. For example, `1INCHEUR`
   witnesses `1INCH` → `1inch` and `ZEUR` → `euro`; `KSM` is handled separately below.
3. Seventeen additional aliases were checked against the venue's named projects
   and existing Catalogue asset descriptions, rather than accepting ticker equality.
   [Kraken's supported assets](https://support.kraken.com/articles/360000678446-cryptocurrencies-available-on-kraken)
   supplies the full-name evidence. The table below records these aliases.

| Native ID | Existing Catalogue asset |
| --- | --- |
| `2Z` | `doublezero` |
| `ALCX` | `alchemix` |
| `BAL` | `balancer` |
| `DRV` | `derive` |
| `FXS` | `frax-share` |
| `GHST` | `aavegotchi` |
| `KSM` | `kusama` |
| `ORCA` | `orca` |
| `SONIC` | `sonic-svm` |
| `SPX` | `spx6900` |
| `STG` | `stargate-finance` |
| `SUSHI` | `sushi` |
| `TBTC` | `threshold-bitcoin` |
| `USELESS` | `useless-coin` |
| `WAXL` | `axelar` |
| `WOO` | `woo-network` |
| `ZORA` | `zora` |

The Frax governance record already documents its FXS → FRAX rename; `FXS` does not
map to either Frax dollar stablecoin. Kraken's [tBTC statement](https://assets-cms.kraken.com/files/51n36hrp/facade/eed1a4382e288404a98fac796134f15143bf75b8.pdf)
identifies Threshold's tokenized bitcoin. Its [WOO statement](https://assets-cms.kraken.com/files/51n36hrp/facade/c66803d9cf6f3963f4e76dd5757414d8114b2c0f.pdf)
identifies the existing WOO project. Its [WAXL statement](https://assets-cms.kraken.com/files/51n36hrp/facade/0a6c8ca8931219add57746db950aa465682d4ea1.pdf)
identifies the Axelar-issued ERC-20 representation of AXL; this follows Catalogue's
existing Axelar identity and native/issuer deployment policy. Sonic SVM (`SONIC`)
remains distinct from Sonic Labs (`S`).

The venue metadata comes from validated `typed-kraken 0.4.0` responses through
`tribulnation-kraken 0.3.0`:
[Assets](https://docs.kraken.com/api-reference/market-data/get-asset-info) and
[AssetPairs](https://docs.kraken.com/api-reference/market-data/get-tradable-asset-pairs).
The SDK's internal/display AssetPairs join supplies the exact native fields and
market IDs; no generic X/Z-prefix stripping or pair-name identity guessing is used.

## Excluded collisions

| Symbol | Kraken listing | Existing Catalogue asset not used |
| --- | --- | --- |
| `MET` | Meteora | `metronome` |
| `OMNI` | Omni | `omnicat` |
| `VELO` | Velo | `velodrome` |
| `MIM` | Magic Internet Money on Bitcoin | Abracadabra `magic-internet-money` stablecoin |

Even a matching full name can collide: Kraken's MIM listing is on Bitcoin, while
Catalogue's MIM is Abracadabra's USD stablecoin. A public SDK ticker read returned
`0.0005371000 USD` for Kraken `MIMUSD`; the price corroborates the identity mismatch
but is not used as the identity rule. All four symbols remain untranslated.
See [asset traps](../asset-traps.md#kraken-symbol-and-name-collisions).

## New active instruments

- `2Z`: `2ZEUR`, `2ZUSD`
- `ALCX`: `ALCXEUR`, `ALCXUSD`
- `BAL`: `BALEUR`, `BALUSD`
- `DRV`: `DRVEUR`, `DRVUSD`
- `FXS`: `FXSEUR`, `FXSUSD`
- `GHST`: `GHSTEUR`, `GHSTUSD`
- `KSM`: `KSMEUR`, `KSMGBP`, `KSMUSD`
- `ORCA`: `ORCAEUR`, `ORCAUSD`
- `SONIC`: `SONICUSD`
- `SPX`: `SPXEUR`, `SPXUSD`
- `STG`: `STGEUR`, `STGUSD`
- `SUSHI`: `SUSHIEUR`, `SUSHIUSD`
- `TBTC`: `TBTCEUR`, `TBTCUSD`, `TBTCXBT`
- `USELESS`: `USELESSEUR`, `USELESSUSD`
- `WAXL`: `WAXLEUR`, `WAXLUSD`
- `WOO`: `WOOEUR`, `WOOUSD`
- `ZORA`: `ZORAEUR`, `ZORAUSD`

## Validation

1. Full Catalogue validation passes using the repository virtualenv.
2. All 35 added pairs were re-read as `online` through the SDK, with nonempty
   public bid/ask tickers and one-level books. No private account calls were made.
3. `scripts/instrument_urls.py` generated all 35 URLs. Every URL was checked against
   the live Kraken display symbol; no unrelated instrument files changed.
4. SDK Catalogue coverage confirms the counts above. The SDK's read-only Kraken
   consistency collector and policy verifier passed against this candidate data.
   This is Catalogue qualification, not a replacement SDK release attestation.

The remaining 474 asset IDs require additional project identity work and, where
no matching identity exists, new canonical assets. Existing symbol collisions, tokenized
securities and renamed projects must be handled explicitly before their pairs can
be added. Passing this bounded pass does not declare complete Kraken coverage.
