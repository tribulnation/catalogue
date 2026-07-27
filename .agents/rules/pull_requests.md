# Pull Request Workflow

Follow this for every PR that adds or changes catalogue data (assets, networks, platforms, translations, instruments).

## Sourcing

- Every factual claim (display name, symbol, chain id, external IDs, etc.) must come from a primary or reliable source: the project's official site, official docs/brand kit, CoinGecko/CoinMarketCap, a block explorer, or an exchange's own API/docs.
- Do not guess or infer IDs, symbols, or chain parameters from ticker names or memory.
- Keep track of every source URL used while researching — they go in the PR description (see below).

## Validation

Before opening a PR, run:

```sh
PYTHONPATH=lib/src .venv/bin/python scripts/validate.py
```

Fix any errors. Include the final asset/platform counts in the PR description.

## PR description

Every PR must include:

1. **Summary** — what was added/changed and why, one bullet per file/concept.
2. **Sources** — a bulleted list of every URL used to verify the content (official site, CoinGecko/CoinMarketCap page, docs, brand kit, original icon source, etc.), so it can be verified without redoing the research.
3. **Icon preview** (only when an icon was added or changed):
   - Render the icon as it will actually display, e.g. `![<id> icon](https://raw.githubusercontent.com/tribulnation/catalogue/<branch>/icons/asset/<id>.svg)`.
   - Also render it **clipped to its inscribed circle** (see `.agents/rules/icons.md` for the maskability check) so the reviewer can confirm nothing is cropped, without opening an editor. Generate this by wrapping the icon in a `clip-path` circle, commit it as a scratch file (e.g. under `.github/pr-previews/`), reference it via a raw GitHub link pinned to that commit SHA, then delete the scratch file in the next commit — the image stays reachable through git history but the branch's working tree stays clean.
4. **Test plan** — confirmation that validation passed, with counts.

## After opening the PR

- Call `subscribe_pr_activity` on the PR so review comments and CI failures are delivered automatically.
- When addressing a review comment about an icon change, reply with an updated circle-cropped preview using the same scratch-file-then-delete technique, so the fix can be visually confirmed in the same comment thread.

## `1000X`-style tickers: multiplier contract vs. real distinct asset

Exchanges use `1000X`/`kX`-style ticker prefixes (`1000BONK`, `1000PEPE`, `kSHIB`, `1000SATS`, ...) for two unrelated reasons. Telling them apart matters — treating one as the other either loses information or invents a fake asset:

1. **Synthetic contract multiplier** (only ever seen on **perpetual/derivatives** contracts): the exchange scales the contract's quoted price/size by N (usually 1000x) purely because the real token's unit price is a tiny fraction of a cent — there is no separate token to hold, it is purely a derivatives-contract convention. Example: Binance/Bybit's `1000BONKUSDT`/`1000PEPEUSDT` perpetuals — Binance's own docs classify these as "Multiplier Denominated Token" contracts tracking the real BONK/PEPE price.
   - Resolve the real underlying asset as `base`, and set the `Perpetual` schema's `multiplier` field on the instrument (e.g. `{"base": "bonk", ..., "multiplier": 1000}`). See `data/instruments/perpetual/hyperliquid.json`'s `kBONK`/`kSHIB`/`kFLOKI` entries for the reference convention.
   - Never add these to `data/asset_translations/<platform>.json` — a translation entry means "this symbol IS this asset" (1:1), and e.g. `1000BONK: bonk` would silently lose the multiplier for any other consumer of that translation.
   - There is no `multiplier` field on `Spot` — spot markets always trade the real, deliverable unit, so a genuine contract-multiplier concept doesn't apply there. If you think you've found a spot instrument that needs one, you've almost certainly found case 2 instead.

2. **A real, distinct, holdable token** whose name happens to include a number: e.g. Binance's spot `1000SATS` is an actual BRC-20 token ("SATS (Ordinals)") with its own supply and its own independent CoinGecko/CoinMarketCap listing — the "1000" is part of its identity, not a multiplier of some other asset.
   - This is a normal asset. Add it to `data/assets/<id>.json` like any other and reference it directly as `base`/`quote` — no multiplier involved.

**How to tell which case you're in:** check whether the ticker has its own independent CoinGecko/CoinMarketCap listing distinct from the "unscaled" asset. If yes, it's case 2 (a real asset — add it). If the ticker only ever appears as a derivatives contract and there's no separate coin listing, it's case 1 (a multiplier — use the `Perpetual.multiplier` field, do not create a new asset or translation).

## Branching

- Only push to the designated branch for this repo/session. If the branch's prior PR has already been merged, restart it from the latest default branch before adding new work (`git fetch origin main && git checkout -B <branch> origin/main`) rather than stacking on merged history.
- Keep unrelated changes (e.g. docs/skill fixes vs. data additions) in separate PRs when practical — ask first if it's unclear whether to bundle them.
