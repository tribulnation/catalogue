import { flattenInstruments, INSTRUMENT_PAGE_SIZE, type PlatformCount } from '$lib/instruments';

const kinds = ['spot', 'perpetual', 'debt', 'pools'];

export const entries = () => kinds.map((kind) => ({ kind }));

// Only the first page is embedded in the prerendered HTML; the page fetches the rest
// from the per-platform API files once it has loaded.
export async function load({ fetch, params }) {
	const { kind } = params;
	const platforms: PlatformCount[] = await fetch(`/api/v1/instruments/${kind}.json`).then((r) =>
		r.json()
	);

	const firstPage = [];
	for (const { platform } of platforms) {
		const data = await fetch(`/api/v1/instruments/${kind}/${platform}.json`).then((r) => r.json());
		firstPage.push(...flattenInstruments(platform, data));
		if (firstPage.length >= INSTRUMENT_PAGE_SIZE) break;
	}

	return { kind, platforms, firstPage: firstPage.slice(0, INSTRUMENT_PAGE_SIZE) };
}
