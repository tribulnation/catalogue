export const INSTRUMENT_PAGE_SIZE = 100;

export type PlatformCount = { platform: string; count: number };

/** An instrument from the per-platform API files; fields present depend on the kind. */
export type Instrument = {
	id: string;
	_platform: string;
	url?: string;
	delisted?: boolean;
	base?: string;
	quote?: string;
	settlement?: string;
	multiplier?: string | number;
	name?: string;
	asset?: string;
	assets?: string[];
};

type InstrumentFile = Record<string, Omit<Instrument, '_platform'>>;

export type SearchableInstrument = Instrument & { _search: string };

export function flattenInstruments(platform: string, items: InstrumentFile): Instrument[] {
	return Object.values(items).map((inst) => ({ ...inst, _platform: platform }));
}

/** Loads every instrument of a kind in the browser, with a lowercase search string built once per row. */
export async function fetchInstruments(
	kind: string,
	platforms: PlatformCount[]
): Promise<SearchableInstrument[]> {
	const lists = await Promise.all(
		platforms.map(({ platform }) =>
			fetch(`/api/v1/instruments/${kind}/${platform}.json`)
				.then((r) => r.json())
				.then((data: InstrumentFile) =>
					Object.values(data).map((inst) => ({
						...inst,
						_platform: platform,
						_search: `${JSON.stringify(inst)} ${platform}`.toLowerCase()
					}))
				)
		)
	);
	return lists.flat();
}
