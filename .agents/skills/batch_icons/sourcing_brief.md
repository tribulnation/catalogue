# Icon sourcing brief

Hand this to each sourcing agent, with its own list of asset ids and its own
report path. Work in the repo root. `.agents/rules/icons.md` is binding.

For each asset id assigned to you:

1. Read `data/assets/<id>.json` — display name, symbol, `external` ids, `urls`.
   Identify the project from that, never from the ticker: tickers collide.
2. Find a real SVG logo. Never hand-draw one; never embed or trace a PNG unless
   nothing vector exists anywhere (say so in your report when you do). In order:
   - Bit2Me: fetch `https://bit2me.com/es/precio/<slug>` and grep for
     `assets.bit2me.com/crypto-icons/v8/svg/<sym>-circle-solid-default.svg`.
   - TradingView: `https://s3-symbol-logo.tradingview.com/crypto/XTVC<SYMBOL>--big.svg`.
     Commodities use a bare slug instead: `.../natural-gas--big.svg`.
     TradingView's scanner API resolves a market's real `base_currency_logoid`,
     which is how you tell a collision from the genuine mark.
   - The project's own site, docs, brand kit, app bundle or GitHub org.
   - A token-list repo, when the file is clearly the right project.
3. **Verify identity before standardising.** Render the candidate and compare it
   against the project's own site and its CoinGecko/CoinMarketCap artwork (the
   ids are in the asset json). Real collisions found this way: TradingView's
   `RETH` is a meme token, `BOLD` a panther, `DCC` is DogeConnect, `OMNI` is
   Omni Network, `AURA` a different Aura, `SHM` renders a burrito. If the only
   candidate is the wrong project, that asset is a skip, not a guess.
4. Standardise per `.agents/rules/icons.md`: square `viewBox` with no
   `width`/`height`, square background rect in the brand colour (white when the
   glyph is dark or multicolour), glyph centred inside the safe zone, no
   `<?xml?>` prolog, no `<style>` blocks or CSS classes, no nested `<svg>`,
   unused ids stripped and used ones shortened, 2-space indent. Bit2Me icons are
   a circle on transparent: keep the art, add the square background behind it.
   `icons/asset/xrp.svg`, `tether.svg` and `wrapped-bitcoin.svg` are the house
   style. Measure the glyph rather than eyeballing it —
   `.agents/skills/batch_icons/scripts/fit_icon.py` does the centring and scaling.
5. Save as `icons/asset/<id>.svg`. **Do not edit any JSON and do not run git** —
   the orchestrator wires the `icon` fields in one pass (`wire_icons.py`), which
   is what keeps parallel agents from fighting over the same files.
6. Check each file parses: `python3 -c "import xml.dom.minidom,sys;
   xml.dom.minidom.parse(sys.argv[1])" icons/asset/<id>.svg`, and look at it
   rendered — both square and circle-masked.

Report as JSON to the path you were given:

```json
[{"id": "...", "status": "added|skipped", "source": "<url the svg came from>",
  "note": "why skipped, or anything the reviewer should double-check"}]
```

Skipping is a good outcome when no trustworthy vector exists. Say what you tried.
