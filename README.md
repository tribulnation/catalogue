# Tribulnation Catalogue

> Central catalogue of (crypto-)assets, platforms and networks.

## Adding Data

- Assets: `data/assets`
- Platforms: `data/platforms`
- Networks: `data/networks`
- Network translations: `data/network_translations`
- Asset translations: `data/asset_translations`
- Icons: `icons`

The validate the data running:

```bash
python scripts/validate.py
```

## Loading Data

```bash
pip install -e lib
```

```python
from tribulnation.catalogue import load

catalogue = load.all('data')
```
