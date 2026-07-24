---
name: Propose Catalogue Additions
description: Survey the catalogue for notable missing assets, networks, or trading platforms and add them, one PR per item.
---

Use this for open-ended "find something to add" runs (e.g. a scheduled sweep), as opposed to a specific item requested by name.

1. Take stock of what already exists:
   - `ls data/assets`, `ls data/platforms`, `data/platforms/order.txt`.
   - `ls data/instruments/spot`, `ls data/instruments/perpetual` for exchange coverage.

2. Find gaps against well-known projects: top assets by market cap (CoinGecko/CoinMarketCap rankings), major blockchain networks, and large CEX/DEX venues not yet in `data/platforms`. Cross-check each candidate against `data/assets/*.json` and `data/platforms/*.json` before treating it as missing — some assets exist under a different id than the obvious slug (e.g. check `external.coingecko` values too, not just filenames).

3. Pick up to 10 candidates per run, prioritizing:
   - Clear, verifiable primary sources (official site, CoinGecko/CoinMarketCap, chain registries/explorers).
   - A genuine, findable SVG icon (see `.agents/rules/icons.md` — skip or flag items with no suitable vector logo rather than fabricating one).
   - Avoiding anything requiring subjective/contested judgment calls (e.g. disputed rebrands, unverifiable chain IDs) — skip those and note why.

4. For each candidate, use the matching skill (`create_asset`, `create_network`, or `create_platform`), which in turn follows `.agents/rules/pull_requests.md` and `.agents/rules/icons.md`.

5. Open **one PR per item**, not a combined PR — this keeps review small and independent per candidate. Restart the branch from the latest default branch before each item if a previous item in the same run has already merged (see the branching section of `.agents/rules/pull_requests.md`).

6. At the end of the run, summarize: what was added (with PR links), what was considered but skipped, and why.
