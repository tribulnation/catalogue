# Deribit remaining market coverage — 2026-09-21

Adds 38 linear perpetuals, 37 canonical reference assets and 36 asset aliases on
Catalogue `2ad44d5`. All 36 market omissions recorded on September 19 are now
mapped; EURC and COIN50 are additional current listings. Supported spot coverage remains
19/19. Current perpetual discovery coverage rises from 90/129 to 128/129.

## Identity evidence

1. [Deribit's named asset register](https://support.deribit.com/hc/en-us/articles/25944547269277-Listed-Virtual-Asset-Details)
   identifies the crypto projects and equity/ETF references. The companion JSON
   records each accepted native symbol, canonical ID and instrument. New records
   include 16 crypto assets, 20 equity/ETF references and one index reference.
2. Each added perpetual has an exact base-asset UUID match in
   [Coinbase International's instrument metadata](https://api.international.coinbase.com/api/v1/instruments),
   the index source named in [Deribit's specifications](https://support.deribit.com/hc/en-us/articles/31424969384605-Linear-Perpetual).
   Selection uses active linear perpetuals with equal native quote and settlement
   currencies. Exchange identity remains `perp`; settlement is USDC.
3. `1000MOG` references Mog Coin with `multiplier: 1000`, confirmed by Coinbase's
   `base_asset_multiplier`. No unscaled `1000MOG` or unnecessary `MOG` currency
   alias is introduced. Contract quantity increments do not become price multipliers.
4. `SOXL` references the [Direxion ETF](https://www.direxion.com/product/daily-semiconductor-bull-bear-3x-etfs),
   whose share price already reflects its daily leverage. Its perpetual has no
   extra 3x multiplier. `DRAM`, `EWY`, `QQQ` and `SPY` have separate ETF identities;
   `DRAM` is the [Roundhill Memory ETF](https://www.roundhillinvestments.com/etf/dram/).
   ETFs use the existing `stock` schema category with an `ETF` tag.
5. ARM, TSM and SKHY use separate depositary-receipt reference assets. The
   [Arm investor FAQ](https://investors.arm.com/investor-info/faqs) and
   [TSMC investor FAQ](https://investor.tsmc.com/english/faq) establish the US listings;
   Deribit explicitly identifies SKHY as the ADR. Domestic shares are not added as
   interchangeable aliases. CRCL is [Circle Internet Group](https://www.circle.com/pressroom/circle-reports-second-quarter-2026-results),
   distinct from its issued stablecoins and fund assets.
6. BILL is Billions Network; PRL is Perle; CHIP is USD.AI's governance token.
   They are not Bill Holdings stock, Pearl, or a dollar stablecoin. EDGEX is
   [edgeX's venue-specific ticker](https://www.coinbase.com/en-ca/price/edgex)
   for the EDGE token. BASED1 is [Based One](https://www.coinbase.com/en-es/price/based-eth-token),
   corroborated by the Ethereum contract in retained Coinbase currency metadata
   (`0x4f2b33840227DDD0e28da8d4185D6fa07ADfed87`). No on-chain address translations
   are introduced here.
7. Shared crypto definitions are identical to the corresponding Kraken/KuCoin
   follow-up records. Existing provider IDs are reused only where independently
   corroborated; other new records omit provider IDs. The asset register's linked
   CoinGecko slugs are not treated as infallible identifiers.

## Asset descriptions and project links

All 37 new reference assets include an English description and an official
project, company, fund issuer or index publisher link. Documentation and
community links are labeled accordingly. Descriptions distinguish token utility,
fund shares and equity references; shared records use identical metadata across
the venue follow-ups. This correction changes no identity or instrument fields.

## Retained earn and transfer coverage

| Dataset | Observations | Fully resolved |
| --- | ---: | ---: |
| Deribit earn | 52 | 52 |
| Deribit deposits | 61 | 54 |
| Deribit withdrawals | 61 | 54 |
| Coinbase earn | 2 | 2 |

These are September 19 retained observations, not fresh authenticated account
requests. Asset, optional fee/yield asset and network must all resolve for a row
to count as fully resolved. This change adds no earn/transfer aliases: their
remaining Deribit failures are the seven SDK currency fallbacks masquerading as
network IDs (`BUIDL`, `EURR`, `MATIC`, `SEI`, `STETH`, `USDE`, `USYC`). Their real
route network must come from the SDK before Catalogue can map it. See
[the earlier source-gap evidence](https://github.com/tribulnation/catalogue/issues/122#issuecomment-5716869876).
Coinbase ETH/CBETH earn coverage is already complete on the merged baseline.

## Explicit remaining market work

COIN50 has a distinct `coinbase-50-index` record, confirmed by the
[index publisher](https://www.coinbase.com/coin50), the native asset UUID and
[Coinbase's product specifications](https://help.coinbase.com/en/international-exchange/perpetual-futures-basics/perpetual-futures-product-specifications).
The optional category is omitted because the current enum has no index value;
the record uses an Index tag and does not claim to be a token or fund share.

`OPENAI_USDC-PERPETUAL` remains unresolved: its synthetic pre-IPO reference needs
explicit share-unit/valuation and lifecycle modeling before it can share a
canonical price identity. It is not represented as ordinary publicly traded
OpenAI stock. See [Deribit's RWA specifications](https://support.deribit.com/hc/en-us/articles/38325634622493-RWA-Perpetual).

## Validation

1. Full Catalogue validation passes; instrument URLs are generated with the
   repository script.
2. The companion JSON retains native identity evidence, source URLs, metadata
   fingerprints and exact unresolved identifiers.
3. Terminal refresh and serving replay remain subsequent integration work after
   these PRs merge. This branch does not modify Terminal or its local database.

The live SDK consistency run and its offline fingerprint/policy verifier pass.
Check statuses: `{"pass": 317}`. Policy deferrals do not represent
resolved mappings. Reproduce from the SDK checkout:

```sh
.venv/bin/sdk-dev test consistency deribit --catalogue ../catalogue-deribit-gaps/data --output /tmp/deribit-remaining-review
.venv/bin/sdk-dev results verify /tmp/deribit-remaining-review --catalogue ../catalogue-deribit-gaps/data
```

## External identifiers

36 of 37 new assets have at least one external ID.
The companion JSON records provider endpoints and identity checks for added IDs.
CI now checks new assets for descriptions, URLs and external IDs against the PR base.

COIN50 is the sole exception, tracked in [#152](https://github.com/tribulnation/catalogue/issues/152). Yahoo search and the `^COIN50` chart returned no match; MarketVector publisher identifiers are recorded in that issue.
