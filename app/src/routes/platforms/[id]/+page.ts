export async function load({ fetch, params }) {
	const platform = await fetch(`/api/v1/platforms/${params.id}.json`).then((r) => r.json());
	return { platform };
}
