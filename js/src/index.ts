export type {
  AssetPeg, ExternalIds, AssetSummary, AssetDetail,
  PlatformKind, PlatformSummary, PlatformDetail,
  InstrumentPlatformEntry, InstrumentKind, InstrumentRole, InstrumentReference,
  SpotInstrument, PerpetualInstrument, DebtInstrument, PoolInstrument,
  SpamAddress, Stats,
} from './types.js';

import type {
  AssetSummary, AssetDetail,
  PlatformSummary, PlatformDetail,
  InstrumentPlatformEntry, InstrumentReference,
  SpotInstrument, PerpetualInstrument, DebtInstrument, PoolInstrument,
  SpamAddress, Stats,
} from './types.js';

export const DEFAULT_BASE_URL = 'https://catalogue.tribulnation.com/api';

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`GET ${url} → ${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export class Catalogue {
  private readonly base: string;

  // Lazy caches — fetched at most once per instance
  private _assets?: Promise<Map<string, AssetSummary>>;
  private _platforms?: Promise<Map<string, PlatformSummary>>;
  private _symbols?: Promise<Record<string, string[]>>;

  constructor(base = DEFAULT_BASE_URL) {
    this.base = base;
  }

  private assetsMap(): Promise<Map<string, AssetSummary>> {
    this._assets ??= get<AssetSummary[]>(`${this.base}/assets.json`)
      .then(list => new Map(list.map(a => [a.id, a])));
    return this._assets;
  }

  private platformsMap(): Promise<Map<string, PlatformSummary>> {
    this._platforms ??= get<PlatformSummary[]>(`${this.base}/platforms.json`)
      .then(list => new Map(list.map(p => [p.id, p])));
    return this._platforms;
  }

  private symbolsIndex(): Promise<Record<string, string[]>> {
    this._symbols ??= get(`${this.base}/indexes/symbols.json`);
    return this._symbols;
  }

  // ── Search ────────────────────────────────────────────────────────

  /** Find assets matching a ticker symbol (e.g. "BTC"). */
  async findBySymbol(symbol: string): Promise<AssetSummary[]> {
    const [symbols, assets] = await Promise.all([this.symbolsIndex(), this.assetsMap()]);
    return (symbols[symbol] ?? []).map(id => assets.get(id)).filter(Boolean) as AssetSummary[];
  }

  // ── Assets ────────────────────────────────────────────────────────

  async fetchAssets(): Promise<AssetSummary[]> {
    return [...(await this.assetsMap()).values()];
  }

  fetchAsset(id: string): Promise<AssetDetail> {
    return get(`${this.base}/assets/${id}.json`);
  }

  // ── Platforms ─────────────────────────────────────────────────────

  async fetchPlatforms(): Promise<PlatformSummary[]> {
    return [...(await this.platformsMap()).values()];
  }

  fetchPlatform(id: string): Promise<PlatformDetail> {
    return get(`${this.base}/platforms/${id}.json`);
  }

  // ── Instruments ───────────────────────────────────────────────────

  getSpotPlatforms(): Promise<InstrumentPlatformEntry[]> {
    return get(`${this.base}/instruments/spot.json`);
  }

  getSpotInstruments(platform: string): Promise<Record<string, SpotInstrument>> {
    return get(`${this.base}/instruments/spot/${platform}.json`);
  }

  getPerpetualPlatforms(): Promise<InstrumentPlatformEntry[]> {
    return get(`${this.base}/instruments/perpetual.json`);
  }

  getPerpetualInstruments(platform: string): Promise<Record<string, PerpetualInstrument>> {
    return get(`${this.base}/instruments/perpetual/${platform}.json`);
  }

  getDebtInstruments(platform: string): Promise<Record<string, DebtInstrument>> {
    return get(`${this.base}/instruments/debt/${platform}.json`);
  }

  getPoolInstruments(platform: string): Promise<Record<string, PoolInstrument>> {
    return get(`${this.base}/instruments/pools/${platform}.json`);
  }

  getAssetInstruments(assetId: string): Promise<InstrumentReference[]> {
    return get(`${this.base}/instruments/index/${assetId}.json`);
  }

  // ── Spam ──────────────────────────────────────────────────────────

  getSpam(platform: string): Promise<Record<string, SpamAddress>> {
    return get(`${this.base}/spam/${platform}.json`);
  }

  // ── Stats ─────────────────────────────────────────────────────────

  fetchStats(): Promise<Stats> {
    return get(`${this.base}/stats.json`);
  }
}
