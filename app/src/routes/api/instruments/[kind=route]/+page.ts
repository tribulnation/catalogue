const allowed = new Set(['spot', 'perpetual', 'debt', 'collateral', 'pools']);

export async function load({ fetch, params }) {
	if (!allowed.has(params.kind)) {
		return { kind: params.kind, platforms: [] };
	}
	const platforms = await fetch(`/api/instruments/${params.kind}.json`).then((response) =>
		response.json()
	);
	return { kind: params.kind, platforms };
}
