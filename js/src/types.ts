export type AssetPeg = {
  asset: string
}

export type ExternalIds = {
  coingecko?: string
  coinmarketcap?: string
}

export type AssetSummary = {
  id: string
  display_name: string
  symbol: string
  icon?: string
  tags?: string[]
  pegged_to?: AssetPeg
}

export type AssetDetail = AssetSummary & {
  about?: Record<string, string>
  urls?: Record<string, string>
  external?: ExternalIds
}

export type PlatformKind = 'blockchain' | 'cex' | 'dex'

export type PlatformSummary = {
  id: string
  display_name: string
  kind: PlatformKind
  icon?: string
}

export type PlatformDetail = PlatformSummary & {
  about?: Record<string, string>
  urls?: Record<string, string>
  native_asset?: string
  category?: string
  namespace?: string
  chain_id?: number | string
}

export type InstrumentPlatformEntry = {
  platform: string
  count: number
}

export type SpotInstrument = {
  id: string
  base: string
  quote: string
  exchange?: string
}

export type PerpetualInstrument = {
  id: string
  base: string
  quote: string
  settlement: string
  exchange?: string
}

export type DebtInstrument = {
  id: string
  asset: string
  name: string
}

export type PoolInstrument = {
  id: string
  assets: string[]
  name: string
}

export type InstrumentKind = 'spot' | 'perpetual' | 'debt' | 'pool'
export type InstrumentRole = 'base' | 'quote' | 'settlement' | 'asset'

export type InstrumentReference = {
  kind: InstrumentKind
  platform: string
  id: string
  role: InstrumentRole
}

export type SpamAddress = {
  reason?: string
  source?: string
  reported_at?: string
}

export type Stats = {
  assets: number
  platforms: number
  blockchains: number
  cexs: number
  dexs: number
  asset_translations: number
  network_translations: number
  spot_instruments: number
  perpetual_instruments: number
  assets_with_icons: number
  assets_with_external_ids: number
  assets_with_pegs: number
  spam_addresses: number
}
