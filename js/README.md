# @tribulnation/catalogue

[![npm](https://img.shields.io/npm/v/@tribulnation/catalogue)](https://www.npmjs.com/package/@tribulnation/catalogue)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/tribulnation/catalogue/blob/main/LICENSE)

JavaScript / TypeScript client for the [Tribulnation Catalogue](https://github.com/tribulnation/catalogue) — a typed, open catalogue of crypto assets, trading platforms, and instrument mappings.

## Install

```bash
npm install @tribulnation/catalogue
```

## Usage

```typescript
import { Catalogue } from '@tribulnation/catalogue';

const client = new Catalogue();
```

### Find by symbol

```typescript
const matches = await client.findBySymbol('BTC');
// → AssetSummary[]

matches[0].id           // "bitcoin"
matches[0].display_name // "Bitcoin"
matches[0].icon         // "https://catalogue.tribulnation.com/icons/asset/bitcoin.svg"
```

### Fetch asset or platform detail

```typescript
const bitcoin  = await client.fetchAsset('bitcoin');
const ethereum = await client.fetchPlatform('ethereum');

bitcoin.about?.en   // full description
ethereum.chain_id   // 1
ethereum.namespace  // "eip155"
```

### Instruments

```typescript
const pairs = await client.getSpotInstruments('mexc');
// → Record<string, SpotInstrument>

const perps = await client.getPerpetualInstruments('dydx');
// → Record<string, PerpetualInstrument>
// PerpetualInstrument includes optional multiplier and delisted status.

// All instruments referencing a given asset
const refs = await client.getAssetInstruments('bitcoin');
// → InstrumentReference[]
```

### Lists

```typescript
const assets    = await client.fetchAssets();    // AssetSummary[]
const platforms = await client.fetchPlatforms(); // PlatformSummary[]
const stats     = await client.fetchStats();     // Stats
```

## Custom base URL

```typescript
const client = new Catalogue('https://my-mirror.example.com/api');
```

The default base URL is `https://catalogue.tribulnation.com/api`.

## Caching

Asset and symbol index fetches are cached per `Catalogue` instance — subsequent calls to `findBySymbol` or `fetchAssets` reuse the same promise without hitting the network again.

## Types

All types are exported from the package root:

```typescript
import type {
  AssetSummary, AssetDetail,
  PlatformSummary, PlatformDetail,
  SpotInstrument, PerpetualInstrument,
  InstrumentReference, Stats,
} from '@tribulnation/catalogue';
```

## Links

- [Full catalogue & API](https://catalogue.tribulnation.com)
- [GitHub](https://github.com/tribulnation/catalogue)
- [Python package](https://pypi.org/project/tribulnation-catalogue/)
