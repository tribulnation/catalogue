---
name: Batch Icons
description: Add icons for many assets at once — derive the mechanical ones, parallelize the rest across agents, and publish a review page for the maintainer.
---

Use this when a lot of assets are missing an icon at once. For a single new
asset, `create_asset` already covers it; for one Aave receipt token,
`create_aave_icon` does. Follow `.agents/rules/icons.md` for every icon and
`.agents/rules/pull_requests.md` for the PR.

Scripts live in `scripts/` next to this file and expect to be run from the repo
root. `fit_icon.py`, `contact_sheet.py`, `build_review.py` and `derive_icons.py`
(for bStocks) need `cairosvg` and `pillow` (`.venv/bin/pip install cairosvg pillow`); the rest are stdlib.

## 1. See what is missing, and how much of it is mechanical

```sh
python3 .agents/skills/batch_icons/scripts/missing_icons.py
```

It groups every asset with no usable icon into four kinds:

- **`bstock`** — a Binance bStock (`<equity>-bstock`). Its icon is the
  underlying stock's glyph in black on Binance yellow, per the house styles in
  `.agents/rules/icons.md`. It is not shared: the stock's own colours never
  carry over.
- **`shared`** — a wrapped, pegged or bridged representation of an asset that
  already has an icon (`wrapped-bnb`, `binance-peg-xrp`, `bridged-usd-coin`).
  These point their `icon` field at the underlying asset's file rather than
  duplicating the artwork; the repo already does this (`usual` and `frax-usd`
  are each referenced by two assets).
- **`aave-frame`** — an Aave receipt token (`aave-<x>`, `wrapped-aave-<x>`),
  built by compositing `<x>`'s glyph into the Aave gradient frame.
- **`source`** — needs a real logo found online. This is the slow part.

## 2. Build the mechanical ones

```sh
python3 .agents/skills/batch_icons/scripts/derive_icons.py            # plan
python3 .agents/skills/batch_icons/scripts/derive_icons.py --apply
```

bStocks are built first, then shared icons, so an Aave frame can be built on
an asset that only just got one. Anything whose underlying asset is still icon-less is
reported as a skip — re-run this after step 3 to pick those up.

Watch for two things when a frame looks wrong:

- **A solid disc with no glyph** means the underlying icon's root `<svg>`
  carried `fill="none"` and the inner markup lost it. `icon_svg.split_root`
  returns those root attributes so the nested element can carry them.
- **A repainted glyph** means the underlying icon uses `<style>` + `class=`.
  Class names are global, so they collide once the markup is re-parented.
  `icon_svg.flatten_styles` inlines them as presentation attributes.

## 3. Parallelize the sourcing

Split the `source` list across several agents — a dozen or so assets each is a
reasonable slice. Give each agent `sourcing_brief.md` (next to this file), its
own list of ids, and its own report path. The brief carries the sourcing order,
the identity check, and the standardisation rules.

Two rules make the parallelism safe:

- Agents write **only** `icons/asset/<id>.svg`. No JSON edits, no git commands.
- You wire the `icon` fields yourself afterwards, in one pass:

```sh
python3 .agents/skills/batch_icons/scripts/wire_icons.py
PYTHONPATH=lib/src .venv/bin/python scripts/validate.py
```

Commit as agents land rather than waiting for all of them.

## 4. Look at what you got

```sh
python3 .agents/skills/batch_icons/scripts/contact_sheet.py --since origin/main --out /tmp/sheet
```

Two PNGs: as authored, and clipped to the inscribed circle. Read the circle
sheet properly — it is the maskability check, and it is where you catch a glyph
that measures 80% wide but whose corners still poke through the mask. Fix those
without re-sourcing:

```sh
python3 .agents/skills/batch_icons/scripts/fit_icon.py --radius icons/asset/<id>.svg
```

## 5. Let the maintainer review the batch

```sh
python3 .agents/skills/batch_icons/scripts/build_review.py \
  --since origin/main --sources <reports-folder> --round r1 --out /tmp/review.html
```

Publish the result with the Artifact tool. Every asset gets a card — both
renders, name, symbol, id, where the artwork came from, a "not accepted" toggle
and a notes box — plus a Copy results button that produces a markdown list of
what was rejected and why. That list is the input to the next round: fix what
came back, then rebuild with `--round r2` and a `--revised` map of
`{"<id>": "what changed"}`, which tags those cards and clears their old marks so
only the changed ones are re-judged.

A batch this size will come back with real mistakes in it — swapped artwork,
a stale mark an exchange feed still serves, a glyph that is off-centre. Expect
the round trip; it is cheaper than a reviewer finding them in the diff.

## 6. Open the PR

Follow `.agents/rules/pull_requests.md`. For a batch, that means:

- Group the summary by kind (sourced / frames / shared) rather than listing
  every asset, but keep the per-asset source URLs — collapse a repeated URL
  pattern to the pattern plus each symbol so every one stays derivable.
- Commit both contact sheets under `.github/pr-previews/`, link them at the
  pinned commit SHA, then delete them in the next commit.
- Say which assets still have no icon and why. "Only raster artwork exists" is
  a legitimate outcome and belongs in the PR, not in a fabricated logo.
- Include validation counts, and state that every icon file parses.
