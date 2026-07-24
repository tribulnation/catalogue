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

## Branching

- Only push to the designated branch for this repo/session. If the branch's prior PR has already been merged, restart it from the latest default branch before adding new work (`git fetch origin main && git checkout -B <branch> origin/main`) rather than stacking on merged history.
- Keep unrelated changes (e.g. docs/skill fixes vs. data additions) in separate PRs when practical — ask first if it's unclear whether to bundle them.
