# KuCoin remaining coverage — 2026-09-21

This follow-up to #130 adds 649 KuCoin asset translations, 100 network translations,
546 spot instruments and 241 linear perpetual instruments against `2ad44d5`.
It includes 641 canonical asset records and 100 blockchain platform records,
reusing byte-identical records from the parallel Kraken and Bybit reviews where
identities overlap. These are reviewable additions, not a claim of exhaustive
coverage or a Terminal deployment.

## Identity evidence

1. The current public [currency inventory](https://api.kucoin.com/api/v3/currencies)
   identifies currencies by full project name and chain-specific deployment. The
   [spot inventory](https://api.kucoin.com/api/v2/symbols) and
   [futures inventory](https://api-futures.kucoin.com/api/v1/contracts/active)
   establish exact native market IDs and base/quote/settlement currencies. Only
   enabled spot and open, undated, non-inverse futures are added.
2. Shared canonical identities were matched by full project name and venue symbol,
   or by exact network plus contract witnesses from Bybit currency metadata. The
   companion JSON records each accepted KuCoin full name and deployment, 187
   cross-venue contract witnesses, reviewed residual identities, public snapshot
   hashes, and every new market's native fields. CoinGecko's coin-name inventory
   corroborates reviewed names; no new external pricing ID is inferred for the
   residual records. Deployment addresses in this report are evidence, not new
   on-chain translations; no EVM address mapping is added.
3. [KuCoin's TON-to-GRAM announcement](https://www.kucoin.com/en-au/announcement/en-kucoin-has-completed-the-rename-of-toncoin-ton-to-gram-gram-160626)
   confirms a 1:1 rename; `GRAM` maps to the existing Toncoin identity.
   [The OpenLedger listing](https://www.kucoin.com/announcement/ph-openledger-open-gets-listed-on-kucoin-world-premiere)
   identifies `OPEN`, and [the CHIP listing](https://www.kucoin.com/announcement/en-world-premiere-usd-ai-chip-listed-on-kucoin)
   identifies CHIP as USD.AI governance, distinct from its stablecoin.
4. [United Stables' KuCoin listing](https://www.kucoin.com/announcement/en-united-stables-u-listed-on-kucoin)
   identifies KuCoin `U` as United Stables; `UNION` identifies Union. Other venues'
   `U` is not blindly copied. Likewise KuCoin `VELO` is Velo, not Velodrome;
   `BFC` Bifrost and `BNC` Bifrost Native Coin remain different projects.
   [KuCoin's ETH2-to-ksETH announcement](https://www.kucoin.com/announcement/en-kucoin-is-renaming-eth2-to-kseth)
   establishes a distinct KuCoin custodial staking receipt, mapped as
   `kucoin-staked-ether`, never ordinary ETH. USDP, USTC, Circle xStock, Uranium and
   Matrixdock Gold retain distinct canonical identities without inferred pegs.
5. Network identity is recorded separately from its token. KuCoin's `cfx` and
   `cfxcore` have EVM and `cfx:` address formats, respectively; `avax` uses
   `X-avax` addresses, unlike `avaxc`. Core/eSpace and Avalanche X/C remain distinct.
   [Polkadot's documentation](https://wiki.polkadot.com/learn/how-to/vault-replicate-account/)
   establishes Statemint/Statemine as the two Asset Hubs, separate from the relay
   chains. [KCC](https://docs.kcc.io/developers/network-endpoints),
   [Fraxtal](https://docs.frax.com/fraxtal/network/network-information), and
   [Kava](https://docs.kava.io/docs/ethereum/overview/) supply the verified network
   details used in those records. Other newly named network records omit chain IDs
   and gas-asset claims where not independently established.
6. KuCoin futures `multiplier` converts contract lots to base quantity. It is
   retained in the evidence but never copied into Catalogue's price multiplier.
   Futures-only `XBT` remains an instrument namespace alias, not a wallet alias.
   Existing records are not delisted merely because discovery no longer returns them.

## Retained data resolution

| Dataset | Observations | Fully resolved before | Fully resolved after |
| --- | ---: | ---: | ---: |
| Earn | 193 | 140 | 192 |
| Deposit methods | 948 | 236 | 823 |
| Withdrawal methods | 964 | 226 | 820 |

The retained September 19 identifier observations are replayed offline against the
baseline and proposed mappings. A complete row requires the principal asset,
optional reward/fee asset, and transfer network. Counts are observations, not
unique serving keys. No Terminal data or running service was changed.

The sole remaining earn miss is the literal reward identifier `USDT,U`, attached
to a USDT product. It describes multiple reward currencies and must not be mapped
to one asset. This needs upstream product/SDK representation review, not a fake
Catalogue alias. All retained principal earn assets resolve.

Deposit methods retain 106 asset-unresolved observations and 19 network-unresolved
observations among asset-resolved rows. Withdrawals retain 124 and 20 respectively.
The companion JSON classifies every remaining native asset, market and network;
it includes current currency metadata and counted retained identifier tuples for
reproduction. Network cases include the two Bifrost routes, `hype`, `robinhood`,
and other network/execution-space distinctions requiring further evidence.

Current discovery resolves 870 of 988 spot instruments (324 before) and 430 of 678
supported perpetuals (189 before). The remaining 118 spot and 248 perpetual IDs
are explicitly listed, including futures-only assets absent from the spot currency
inventory and ambiguous/rebranded identifiers. These remain follow-up work.

## Validation

1. Full Catalogue validation and generated instrument URLs pass.
2. `git diff --check` passes.
3. The final public SDK consistency run and offline fingerprint/policy verification
   pass. Check statuses: `{"deferred": 21, "pass": 2644}`. These policy checks do not imply
   exhaustive identity or liquidity coverage.
4. An independent public SDK probe with response validation enabled discovers,
   constructs and reads native tickers for all 546 added spot and 241 added
   perpetual markets; no added market is absent.

[Machine-readable evidence and unresolved identifiers](kucoin-remaining-coverage-2026-09-21.json)

Reproduce SDK checks from the SDK checkout:

```sh
.venv/bin/sdk-dev test consistency kucoin --catalogue ../catalogue-kucoin-gaps/data --output /tmp/kucoin-gaps/consistency-final
.venv/bin/sdk-dev results verify /tmp/kucoin-gaps/consistency-final --catalogue ../catalogue-kucoin-gaps/data
```
