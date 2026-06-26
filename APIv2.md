# Static API Proposal v2

## Routes

### Home `/`

Documentation and overview.

### API `/api`

#### Stats `/api/stats.json`

Global stats about the catalogue.

```ts
type State = {
  assets: number
  platforms: number
  // ...
}
```

### Assets List `/api/assets.json`

A list of all assets with minimal metadata

```ts
type AssetsList = Array<{
  id: string
  display_name: string
  symbol: string
  icon?: string
}>
```

### Assets `/api/assets/<id>.json`

Detailed metadata for a specific asset.

```ts
type Asset = {
  id: string
  display_name: string
  symbol: string
  // ...
}
```

### Platforms List `/api/platforms.json`

A list of all platforms with minimal metadata

```ts
type PlatformsList = Array<{
  id: string
  display_name: string
  icon?: string
}>
```

### Platforms `/api/platforms/<id>.json`

Detailed metadata for a specific platform.

```ts
type Platform = {
  id: string
  display_name: string
  // ...
}
```

### Blockchains List `/api/platforms/blockchains.json`

...

### Centralized Exchanges List `/api/platforms/cexs.json`

...

### Decentralized Exchanges List `/api/platforms/dexs.json`

...


### Translations `/api/translations`

#### Asset Translations `/api/translations/assets/<platform>.json`

...

#### Network Translations `/api/translations/networks/<platform>.json`

...


### Instruments `/api/instruments`

#### Spot Pairs (CEXs/DEXs) `/api/instruments/spot/<platform>.json`

...

#### Perpetual Markets (CEXs/DEXs) `/api/instruments/perpetual/<platform>.json`

...

#### Debt Assets (DEXs/Blockchains) `/api/instruments/debt/<platform>.json`

...

#### Collateral Assets (DEXs/Blockchains) `/api/instruments/collateral/<platform>.json`

...

#### Liquidity Pools (DEXs/Blockchains) `/api/instruments/pools/<platform>.json`

...

#### Instrument Indices `/api/instruments/index/<asset>.json`

All instruments where the given asset is the base/underlying.

...


### Spam Addresses (CEXs/DEXs) `/api/spam/<platform>.json`

...


### Indexes `/api/indexes`

#### Symbols `/api/indexes/symbols.json`

...

#### External IDs `/api/indexes/external/<provider>.json`

...

#### Pegged Assets `/api/indexes/pegs.json`

...