export async function load({ fetch, params }) {
	const platform = await fetch(`/api/platforms/${params.id}.json`).then((r) => r.json());
	return { platform };
}
