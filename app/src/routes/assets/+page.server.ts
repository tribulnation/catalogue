import { ASSET_PAGE_SIZE, type AssetSummary } from '$lib/assets';

// Only the first page is embedded in the prerendered HTML; the page fetches the full
// list from /api/v1/assets.json once it has loaded.
export async function load({ fetch }) {
	const assets: AssetSummary[] = await fetch('/api/v1/assets.json').then((r) => r.json());
	return {
		total: assets.length,
		firstPage: assets.slice(0, ASSET_PAGE_SIZE),
		categories: [...new Set(assets.flatMap((a) => (a.category ? [a.category] : [])))].sort(),
		tags: [...new Set(assets.flatMap((a) => a.tags ?? []))].sort()
	};
}
