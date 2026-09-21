# Kraken remaining markets and transfer identities — 2026-09-21

Adds 421 canonical assets, 427 Kraken asset aliases, 701 spot instruments,
70 USD-settled perpetual instruments, 71 blockchain records and 77 network
aliases against Catalogue `2ad44d5`. Related: [#130](https://github.com/tribulnation/catalogue/issues/130).

## Descriptions and official links

All 421 new assets and 71 new blockchain records include a
project-specific English description and at least one project, issuer,
documentation, source-code, community or verified token-contract link. Link labels identify their purpose.
Source review excludes parked domains and distinguishes similarly named projects;
shared records have identical metadata across all four venue PRs. This correction
changes no asset identity, translation or instrument fields.

## Identity evidence

1. Kraken's current [supported-asset registry](https://support.kraken.com/en-us/articles/360000678446-cryptocurrencies-available-on-kraken)
   supplies explicit full project names, native codes and networks. Exact full-name
   and symbol matches against the retained September 19 CoinGecko registry corroborate
   external IDs where unambiguous. Other explicitly named projects get
   canonical records without guessed external IDs, token contracts or pegs.
2. [Assets](https://api.kraken.com/0/public/Assets) establishes exact native-key to
   `altname` joins. For example, `XMLN` resolves through `MLN` to Enzyme.
   [Kraken's Terra notice](https://support.kraken.com/articles/6548163943956-luna-and-ust-updates-on-kraken-)
   explicitly distinguishes `LUNA` (Terra Classic) from `LUNA2` (Terra).
3. Shared canonical records were compared with the concurrent Bybit, KuCoin and
   Deribit investigations. Kraken `U` is Union, distinct from KuCoin's United
   Stables. Kraken `VELO` is Velo, `VELODROME` is Velodrome; `MET` is Meteora,
   not Metronome; `OMNI` is Omni, not OmniCat. APENFT's current canonical name and
   symbol are AINFT/NFT following the [official rebrand](https://www.kucoin.com/announcement/en-kucoin-supports-the-apenft-nft-rebranding-0112).
4. Stablecoins and staking receipts retain separate identities. These include
   [Quantoz EURQ/USDQ](https://blog.kraken.com/product/asset-listings/eurq-and-usdq-more-stablecoins-available-on-kraken),
   [Liquid Collective LsETH](https://liquidcollective.io/lseth-on-kraken/), LsSOL,
   JitoSOL and Marinade mSOL. No token is collapsed into its reference fiat or
   underlying staked coin. Their issuer/venue references are recorded individually
   in the companion JSON; no peg is inferred for new records.
5. Kraken's `MIM` is the Bitcoin Magic Internet Money project. The
   [project's own history](https://mimwizards.com/) identifies Rune 17 and its
   Kraken listing. It gets `magic-internet-money-bitcoin`, distinct from the
   existing Abracadabra dollar stablecoin.
6. Exact plain blockchain names from retained Kraken WithdrawMethods responses
   become network aliases, with documented blockchain records where necessary.
   Asset Hubs, Enjin Relaychain, Bifrost Kusama and Arbitrum Nova stay distinct
   from their parent or similarly named networks. No EVM IDs, namespaces or
   gas assets are guessed. Existing shared chain definitions are reused.
   Explicit native-USDC and Ink-USDG routes are supported by Kraken's
   [stablecoin network table](https://support.kraken.com/en-us/articles/stablecoins-supported-on-kraken).

## Markets and retained coverage

Spot additions join exact native `base`/`quote` values from current
[AssetPairs](https://api.kraken.com/0/public/AssetPairs), use `altname` as the
instrument ID and require `online` status. Perpetual additions follow the
SDK's exact supported instrument/ticker filter: active, unsuspended flexible
perpetuals, USD quote, unit contract size, non-expired and no dated expiry.
Quote and settlement remain USD, and every addition has a generated trading URL.

| Retained dataset | Rows | Primary asset before | Primary asset after | Fully resolved before | Fully resolved after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Earn instruments | 73 | 73 | 73 | 73 | 73 |
| Withdrawal methods | 792 | 271 | 695 | 205 | 668 |

Full resolution requires every primary/fee/yield asset and network identity.
These are retained observation counts, not deduplicated serving rows. The source
object keys are included in the JSON. No Terminal serving replay or deployment
was performed by this PR.

## Remaining identifiers

1. 97 withdrawal observations still lack a primary asset identity. For 64 native
   IDs there is no exact current supported-asset registry entry; historical
   listing/native-alias evidence is still needed. Other cases involve issuer or
   deployment ambiguity, migrations, or same-name tokens. Every remaining ID has
   its observed count, available Kraken name/network, and concrete blocker in the
   companion JSON. These are not marked resolved by a passing coverage policy.
2. 21 distinct network labels remain unresolved: three banking rails, plain
   `Conflux` (Core Space versus eSpace), and 17 composite token routes involving
   `USDC.e`, `USDT0`, `kBTC` or `kHYPE`. Independent global asset/network aliases
   cannot express a delivered token different from the source primary asset.
   Consequently 124 withdrawal observations are not fully resolved.
3. Current discovery still contains 75 unmapped online spot markets and 52
   supported perpetuals. These include unresolved crypto identities, xStocks,
   pre-IPO references, indices and commodity products. No xStock is mapped to an
   ordinary share merely because its name resembles a listed company.

The [companion JSON](kraken-coverage-2026-09-21.json) records every accepted identity,
new native instrument, source URL and snapshot fingerprint, plus all remaining
native asset, network and market IDs.

## Validation

1. Full Catalogue schema/reference/order validation and `git diff --check` pass.
2. All new instrument URLs were generated with `scripts/instrument_urls.py`.
3. Live Kraken SDK consistency and offline input-fingerprint/policy verification
   pass. Policy deferrals are not claims of exhaustive market coverage.

Reproduce the live and offline checks from the SDK checkout:

```sh
.venv/bin/sdk-dev test consistency kraken --catalogue ../catalogue-kraken-gaps/data --output /tmp/kraken-remaining-review
.venv/bin/sdk-dev results verify /tmp/kraken-remaining-review --catalogue ../catalogue-kraken-gaps/data
```

## External identifiers

421 of 421 new assets have at least one external ID.
The companion JSON records provider endpoints and identity checks for added IDs.
CI now checks new assets for descriptions, URLs and external IDs against the PR base.

COPM uses its issuer-verified Polygon contract as a DefiLlama ID. The public pricing adapter supports USD and historical observations; EUR conversion uses the latest published daily FRED USD-per-EUR rate on or before the observation date, which can lag market FX. Missing prices or required FX data produce no quote.

## Pending identity consolidation

The external-ID audit found the following duplicate canonical records. Their consolidation is pending approval; no records have been deleted or references rewritten in this correction.

1. `aligned-layer` → `aligned`.
2. `bos-token` → `bitcoinos`.
3. `moonwalk` → `moonwalk-fitness`.

Resolve these before merging the venue PRs together to avoid duplicate external-provider identities.
