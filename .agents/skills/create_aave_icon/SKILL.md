---
name: Create Aave Icon
description: Create an icon for an Aave receipt token asset (e.g. aave-eth, aave-eurc) by compositing the underlying asset's icon inside the Aave gradient frame.
---

Use this when adding an icon for an Aave receipt token (aToken). The design is: Aave gradient fills the full square, a transparent gap ring separates it from a white inner circle, and the underlying asset's icon sits centered inside.

See `icons/asset/aave-eth.svg` as a reference example.

## Design pattern

- **Canvas**: 200×200, `viewBox="0 0 200 200"`
- **Gradient**: linear, top-left → bottom-right, `#B6509E` → `#2EBAC6` (Aave brand)
- **Frame**: gradient rect masked to exclude a circle of r=88 (the gap boundary)
- **Gap**: r=82–88, transparent (6px ring showing the page background)
- **Inner circle**: white, r=82, for the underlying asset
- **Underlying icon**: centered in the white circle, ~70px wide

## SVG template

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <defs>
    <linearGradient id="aave" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#B6509E"/>
      <stop offset="100%" stop-color="#2EBAC6"/>
    </linearGradient>
    <mask id="frame">
      <rect width="200" height="200" fill="white"/>
      <circle cx="100" cy="100" r="88" fill="black"/>
    </mask>
  </defs>

  <!-- Gradient fills only outside the gap -->
  <rect width="200" height="200" fill="url(#aave)" mask="url(#frame)"/>
  <!-- White inner circle (gap is r=82–88, transparent) -->
  <circle cx="100" cy="100" r="82" fill="white"/>

  <!-- Underlying asset icon, centered -->
  <!-- Replace this with the asset-specific content (see step 2) -->
</svg>
```

## Steps

1. **Find the underlying asset's icon** in `icons/asset/<underlying>.svg`.
   - Read its `viewBox` to understand the coordinate space.
   - Identify the bounds of the actual visual content (ignoring padding/background rect).

2. **Embed the underlying icon** as a nested `<svg>` element inside the template:
   - Set `viewBox` to the trimmed content bounds (excluding the background rect and any padding), so the icon fills the nested area without extra whitespace.
   - Size and position the nested `<svg>` so the content is roughly 70px wide, centered at (100, 100).
   - For the ETH diamond specifically, the trimmed viewBox is `"325 128 627 1022"` and the nested SVG is `x="65" y="43" width="70" height="114"`.
   - Include only the visual paths/polygons from the original icon — omit the background rect.

3. **Save** to `icons/asset/aave-<underlying>.svg`.

4. **Add the icon path** to `data/assets/aave-<underlying>.json`:
   ```json
   "icon": "icons/asset/aave-<underlying>.svg"
   ```

5. **Validate**:
   - `.venv/bin/python validate.py`
