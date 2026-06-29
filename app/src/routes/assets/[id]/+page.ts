export async function load({ fetch, params }) {
	const [asset, instrumentsRes, platforms] = await Promise.all([
		fetch(`/api/v1/assets/${params.id}.json`).then((r) => r.json()),
		fetch(`/api/v1/instruments/index/${params.id}.json`),
		fetch(`/api/v1/platforms.json`).then((r) => r.json())
	]);
	const instruments = instrumentsRes.ok ? await instrumentsRes.json() : [];
	return { asset, instruments, platforms };
}
