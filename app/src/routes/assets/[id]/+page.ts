export async function load({ fetch, params }) {
	const [asset, instrumentsRes] = await Promise.all([
		fetch(`/api/assets/${params.id}.json`).then((r) => r.json()),
		fetch(`/api/instruments/index/${params.id}.json`)
	]);
	const instruments = instrumentsRes.ok ? await instrumentsRes.json() : [];
	return { asset, instruments };
}
