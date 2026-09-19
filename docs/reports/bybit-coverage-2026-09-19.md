# Bybit earn and transfer mappings — 2026-09-19

Adds 133 asset aliases and 19 network aliases. bbSOL, mETH and cmETH receive
separate canonical records. Base: Catalogue `720d172`.

## Identity evidence

1. 130 aliases are derived from exact live Bybit instrument joins to existing
   Catalogue spot/perpetual records, then restricted to identifiers actually
   observed in earn/transfers and present in Bybit coin metadata. Every witness
   for each accepted alias agrees. The companion JSON records the witnesses.
   Contract-scaled bases are not promoted into global unscaled asset aliases.
2. [Bybit's wallet staking documentation](https://www.bybit.com/en/help-center/article/FAQ-Wallet-Staking)
   identifies bbSOL. [Bybit's mETH product](https://www.bybit.com/en/earn/meth-page/)
   and [mETH Protocol](https://www.methprotocol.xyz/) distinguish the staking and
   restaking claims. BBSOL, METH and CMETH are not SOL/ETH, not interchangeable with
   each other, and have no one-to-one underlying-price fallback. CoinGecko IDs
   were verified by project name, not by the reused ticker alone.
3. [Bybit's FXS migration announcement](https://announcements.bybit.com/en/article/token-swap-and-rebranding-of-frax-share-fxs-to-frax-frax--bltf5ddf3022f5bbb29/)
   corroborates FRAX → `frax-share`. The existing SONIC → `sonic-svm` correction
   stays intact; S → `sonic` and network SONIC → `sonic` are separate identities.
4. Each added network code is checked against Bybit's `chainType` description and
   an existing blockchain object. These include HYPEREVM, MOVE, MONAD, BERA,
   CELESTIA, KLAY, SCROLL, TAIKO, VANA and XDC. `coin/query-info` requires
   authentication on the probed host; it was read through the existing SDK setup,
   and only currency/network definitions were used. No account data is retained.

## Remaining work

Earn asset resolution rises from 54 to 177 of 285 retained rows. Complete transfer
resolution rises from 62 to 228 of 569 deposits, and 64 to 224 of 848 withdrawals.
These are observations, not unique assets or deduplicated serving rows.

The companion JSON records all remaining identifiers. In particular, 108 earn
observations still require identity work and new canonical assets. Transfers
also include retired assets and projects absent from Catalogue; their names must
not be inferred from an unrelated venue's reused symbol.

Network gaps requiring separate objects include DOTAH (Polkadot Asset Hub),
XAVAX (Avalanche X-Chain), KAVAEVM, Arc and Codex. XAVAX must not be aliased to
Catalogue's EVM Avalanche C-Chain. `MATIC.E` is a bridged-USDC route whose asset
identity also needs to remain distinct; adding only a Polygon network alias would
hide that distinction.

Coinbase ETH/CBETH are already on main and both retained earn rows resolve; no
additional Coinbase patch is needed. #130 remains open for the remaining gaps.
Terminal integration and serving rebuilds are a later task.

Related: [Catalogue #130](https://github.com/tribulnation/catalogue/issues/130).

## Coverage and validation

| Retained dataset | Rows | Resolved before | Resolved after |
| --- | ---: | ---: | ---: |
| earn_instruments | 285 | 54 | 177 |
| deposit_methods | 569 | 62 | 228 |
| withdrawal_methods | 848 | 64 | 224 |

These checks use the latest retained local observations on September 19. Resolution
requires asset, optional yield/fee asset, and (for transfers) network translations.
No Terminal collection, database changes, serving replay or deduplication was performed.

The [companion JSON](bybit-coverage-2026-09-19.json) records accepted identities, public source URLs,
native market evidence where applicable, and remaining identifiers.

1. Full Catalogue validation passes with `PYTHONPATH=lib/src .venv/bin/python scripts/validate.py`.
2. Instrument URLs are generated with the repository script; `git diff --check` passes.

The SDK consistency run and its offline fingerprint/policy verifier both pass.
Check statuses: `{"pass": 1041}`. Explicit policy deferrals
are not resolved identities or exhaustive coverage. Reproduce from the SDK checkout:

```sh
.venv/bin/sdk-dev test consistency bybit --catalogue ../catalogue-bybit-followup/data --output /tmp/bybit-catalogue-review
.venv/bin/sdk-dev results verify /tmp/bybit-catalogue-review --catalogue ../catalogue-bybit-followup/data
```
