# KuCoin market additions — 2026-09-19

Adds 22 enabled spot pairs and 16 open linear perpetuals with exact SDK exchange
IDs. Adds native FRAX and SONIC asset aliases. Base: Catalogue `720d172`.

## Identity evidence

1. Live spot metadata supplies `symbol`, `baseCurrency` and `quoteCurrency`.
   Futures additionally supply `settleCurrency`, `expireDate`, `isInverse`,
   `multiplier` and `status`. Selection follows the SDK's enabled spot / open
   linear perpetual filters, not symbol suffix guesses.
2. New pairs reuse the venue's already verified canonical aliases. `SONIC` is Sonic
   SVM according to the currency metadata, including its Solana deployment. Sonic
   Labs is the distinct `S` asset. `REDSTONE` remains RedStone; KuCoin's `RED` is a
   different RED TOKEN and remains untranslated. `TSLAX` remains the existing
   Tesla xStock identity, not a Tesla share.
3. [KuCoin's completed FXS migration announcement](https://www.kucoin.com/announcement/en-kucoin-has-completed-the-mainnet-integration-and-rebranding-of-frax-share-fxs-to-frax-frax-260209)
   confirms that current FRAX is the renamed governance token on Fraxtal. This
   resolves the earlier uncertainty in #122: FRAX maps to `frax-share`, not to
   Legacy Frax Dollar or frxUSD. The current currency endpoint's missing contract
   address alone was insufficient; the venue's migration announcement supplies
   the identity evidence.
4. Futures `XBT` denotes Bitcoin in existing contract metadata, but the current
   currency inventory contains no XBT. No global wallet alias is reintroduced.
5. KuCoin's native `multiplier` converts contract lots into base quantity. It is
   not copied into Catalogue's price-index multiplier. New perpetual prices refer
   to one unit of their canonical base asset.

## Remaining work

SDK discovery returned 993 enabled spot markets and 678 supported perpetuals.
After the additions, 667 spot IDs and 489 perpetual IDs still lack mappings.
Their full IDs are retained in the companion JSON. Most require canonical assets
that Catalogue does not yet contain; this is broader catalogue growth, not a
reason to rename SDK symbols.

Earn coverage remains 140 of 193 retained observations. FRAX's asset identity now
resolves on transfer observations, but its Fraxtal network still needs a platform
record, so the complete transfer-row count does not change. Other missing network
objects include Conflux spaces, Kava EVM, KCC, Stable and the two Asset Hubs.
`hype` and `hyperevm` are separate native network entries; neither is guessed to be
an alias for the other. Asset Hub is not collapsed into its relay chain.

No absence from discovery is converted into a delisting. Existing inverse/dated
records and their lifecycle review from the previous KuCoin report remain separate.
Terminal collection and serving integration are deferred.

## Coverage and validation

| Retained dataset | Rows | Resolved before | Resolved after |
| --- | ---: | ---: | ---: |
| earn_instruments | 193 | 140 | 140 |
| deposit_methods | 948 | 236 | 236 |
| withdrawal_methods | 964 | 226 | 226 |

These checks use the latest retained local observations on September 19. Resolution
requires asset, optional yield/fee asset, and (for transfers) network translations.
No Terminal collection, database changes, serving replay or deduplication was performed.

The [companion JSON](kucoin-coverage-2026-09-19.json) records accepted identities, public source URLs,
native market evidence where applicable, and remaining identifiers.

1. Full Catalogue validation passes with `PYTHONPATH=lib/src .venv/bin/python scripts/validate.py`.
2. Instrument URLs are generated with the repository script; `git diff --check` passes.
3. Fresh credential-free SDK discovery, construction and ticker reads pass for every added market with response validation enabled.

The SDK consistency run and its offline fingerprint/policy verifier both pass.
Check statuses: `{"deferred": 19, "pass": 1072}`. Explicit policy deferrals
are not resolved identities or exhaustive coverage. Reproduce from the SDK checkout:

```sh
.venv/bin/sdk-dev test consistency kucoin --catalogue ../catalogue-kucoin-followup/data --output /tmp/kucoin-catalogue-review
.venv/bin/sdk-dev results verify /tmp/kucoin-catalogue-review --catalogue ../catalogue-kucoin-followup/data
```
