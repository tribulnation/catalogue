# Static API Specification

## Conventions

- API files are static JSON generated from `data/`.
- Optional fields are omitted when absent.
- List routes return arrays with minimal metadata.
- Detail routes return full records.
- Route parameters use catalogue IDs unless explicitly noted.

```ts
type Locale = 'ca' | 'es' | 'en'
type Translations = Partial<Record<Locale, string>>

type Urls = Record<string, string>
type IconUrl = string

type ExternalIds = {
  coingecko?: string
}
```

## Routes

### Stats `/api/stats.json`

Global stats about the catalogue.

```ts
type Stats = {
  assets: number
  platforms: number
  blockchains: number
  cexs: number
  dexs: number
  asset_translations: number
  network_translations: number
  assets_with_icons: number
  assets_with_external_ids: number
  assets_with_pegs: number
  spam_platforms: number
}
```

### Assets

#### Assets List `/api/assets.json`

A list of all assets with minimal metadata.

```ts
type AssetsList = Array<{
  id: string
  display_name: string
  symbol: string
  icon?: IconUrl
  tags?: string[]
  pegged_to?: {
    asset: string
  }
}>
```

#### Asset Detail `/api/assets/<id>.json`

Detailed metadata for a specific asset.

```ts
type Asset = {
  id: string
  display_name: string
  symbol: string
  about?: Translations
  tags?: string[]
  urls?: Urls
  icon?: IconUrl
  external?: ExternalIds
  pegged_to?: {
    asset: string
  }
}
```

#### Localized Asset Detail `/api/assets/<id>/<locale>.json`

Detailed metadata for a specific asset and locale. Generated only for locales
available in the asset's `about` field.

```ts
type LocalizedAsset = Omit<Asset, 'about'> & {
  locale: Locale
  about?: string
}
```

### Platforms

#### Platforms List `/api/platforms.json`

A list of all platforms with minimal metadata.

```ts
type PlatformsList = Array<{
  id: string
  display_name: string
  kind: PlatformKind
  icon?: IconUrl
}>
```

#### Platform Detail `/api/platforms/<id>.json`

Detailed metadata for a specific platform.

```ts
type PlatformKind = 'blockchain' | 'cex' | 'dex'
type BlockchainCategory = 'evm'
type BlockchainNamespace = 'bip122' | 'cosmos' | 'eip155' | 'solana'

type BasePlatform = {
  id: string
  display_name: string
  kind: PlatformKind
  about?: Translations
  urls?: Urls
  icon?: IconUrl
}

type Blockchain = BasePlatform & {
  kind: 'blockchain'
  native_asset?: string
  category?: BlockchainCategory
  namespace?: BlockchainNamespace
  chain_id?: string | number
}

type Cex = BasePlatform & {
  kind: 'cex'
}

type Dex = BasePlatform & {
  kind: 'dex'
}

type Platform = Blockchain | Cex | Dex
```

#### Blockchains List `/api/platforms/blockchains.json`

A list of blockchain platforms with minimal metadata.

```ts
type BlockchainsList = Array<{
  id: string
  display_name: string
  kind: 'blockchain'
  icon?: IconUrl
  native_asset?: string
  category?: BlockchainCategory
  namespace?: BlockchainNamespace
  chain_id?: string | number
}>
```

#### Centralized Exchanges List `/api/platforms/cexs.json`

A list of centralized exchange platforms with minimal metadata.

```ts
type CexsList = Array<{
  id: string
  display_name: string
  kind: 'cex'
  icon?: IconUrl
}>
```

#### Decentralized Exchanges List `/api/platforms/dexs.json`

A list of decentralized exchange platforms with minimal metadata.

```ts
type DexsList = Array<{
  id: string
  display_name: string
  kind: 'dex'
  icon?: IconUrl
}>
```

### Translations `/api/translations`

#### Asset Translations `/api/translations/assets/<platform>.json`

Maps platform-specific asset IDs to canonical asset IDs.

```ts
type AssetTranslations = {
  [platform_specific_id: string]: string
}
```

#### Network Translations `/api/translations/networks/<platform>.json`

Maps platform-specific network IDs to canonical platform IDs.

```ts
type NetworkTranslations = {
  [platform_specific_id: string]: string
}
```

### Instruments `/api/instruments`

Instrument routes are platform-specific. Index routes list available platforms
and counts; they do not inline all instrument data.

```ts
type InstrumentPlatformIndex = Array<{
  platform: string
  count: number
}>

type SpotInstrument = {
  id: string
  exchange?: string
  base: string
  quote: string
}

type PerpetualInstrument = {
  id: string
  exchange?: string
  base: string
  quote: string
  settlement: string
}

type DebtInstrument = {
  id: string
  asset: string
  name: string
}

type CollateralInstrument = {
  id: string
  asset: string
  name: string
}

type PoolInstrument = {
  id: string
  assets: string[]
  name: string
}
```

#### Spot Platforms `/api/instruments/spot.json`

Platforms with spot pair data.

```ts
type SpotPlatforms = InstrumentPlatformIndex
```

#### Spot Pairs `/api/instruments/spot/<platform>.json`

Spot pairs for a CEX/DEX, keyed by platform-specific ID.

```ts
type SpotInstruments = {
  [platform_specific_id: string]: SpotInstrument
}
```

#### Perpetual Platforms `/api/instruments/perpetual.json`

Platforms with perpetual market data.

```ts
type PerpetualPlatforms = InstrumentPlatformIndex
```

#### Perpetual Markets `/api/instruments/perpetual/<platform>.json`

Perpetual markets for a CEX/DEX, keyed by platform-specific ID.

```ts
type PerpetualInstruments = {
  [platform_specific_id: string]: PerpetualInstrument
}
```

#### Debt Platforms `/api/instruments/debt.json`

Platforms with debt asset data.

```ts
type DebtPlatforms = InstrumentPlatformIndex
```

#### Debt Assets `/api/instruments/debt/<platform>.json`

Debt assets for a DEX/Blockchain, keyed by platform-specific ID/address.

```ts
type DebtAssets = {
  [address: string]: DebtInstrument
}
```

#### Collateral Platforms `/api/instruments/collateral.json`

Platforms with collateral asset data.

```ts
type CollateralPlatforms = InstrumentPlatformIndex
```

#### Collateral Assets `/api/instruments/collateral/<platform>.json`

Collateral assets for a DEX/Blockchain, keyed by platform-specific ID/address.

```ts
type CollateralInstruments = {
  [address: string]: CollateralInstrument
}
```

#### Pool Platforms `/api/instruments/pools.json`

Platforms with liquidity pool data.

```ts
type PoolPlatforms = InstrumentPlatformIndex
```

#### Liquidity Pools `/api/instruments/pools/<platform>.json`

Liquidity pools for a DEX/Blockchain, keyed by platform-specific ID/address.

```ts
type PoolInstruments = {
  [address: string]: PoolInstrument
}
```

#### Instrument Index `/api/instruments/index/<asset>.json`

All instruments where the given asset is the base, underlying asset, collateral
asset, debt asset, pool constituent, or settlement asset.

```ts
type InstrumentReference = {
  kind: 'spot'
  platform: string
  id: string
  role: 'base' | 'quote'
} | {
  kind: 'perpetual'
  platform: string
  id: string
  role: 'base' | 'quote' | 'settlement'
} | {
  kind: 'debt'
  platform: string
  id: string
  role: 'asset'
} | {
  kind: 'collateral'
  platform: string
  id: string
  role: 'asset'
} | {
  kind: 'pool'
  platform: string
  id: string
  role: 'asset'
}

type InstrumentIndex = Array<InstrumentReference>
```

### Spam Addresses `/api/spam/<platform>.json`

Spam addresses for a DEX/Blockchain, keyed by platform-specific ID/address.

```ts
type SpamAddress = {
  id: string
  reason?: string
  source?: string
  reported_at?: string
}

type SpamAddresses = {
  [address: string]: SpamAddress
}
```

### Indexes `/api/indexes`

#### Symbols `/api/indexes/symbols.json`

Maps symbols to possible canonical asset IDs.

```ts
type SymbolsIndex = {
  [symbol: string]: string[]
}
```

### External IDs `/api/indexes/external/<provider>.json`

Maps third-party registry IDs to canonical asset IDs.

```ts
type ExternalIndex = {
  [provider_specific_id: string]: string
}
```

### Pegged Assets `/api/indexes/pegs.json`

Maps target asset IDs to assets that track or represent them.

```ts
type PegsIndex = {
  [target_asset_id: string]: string[]
}
```

## Build

Recommended build command:

```bash
.venv/bin/python scripts/build_api.py
```

The builder should:

1. Load `data/`.
2. Run validation.
3. Recreate `<output>/api`.
4. Write list, detail, translation, instrument, spam, stats, and index files.
5. Copy or expose icons under `<output>/icons`.
6. Write API folder index pages when generating standalone `public` output.
7. Exit non-zero on validation errors or duplicate external index keys.

The optional `--public-url` argument turns source icon paths such as
`icons/asset/bitcoin.svg` into absolute API URLs such as
`https://tribulnation.github.io/catalogue/icons/asset/bitcoin.svg`. When omitted,
icon paths are root-relative, for example `/icons/asset/bitcoin.svg`.

If a SvelteKit `app/` exists, the default output directory is `app/static`, so
the API is generated at `app/static/api` and icons at `app/static/icons`.
Otherwise the default output directory is `public`.
