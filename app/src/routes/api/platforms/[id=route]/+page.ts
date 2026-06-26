export async function load({ fetch, params }) {
	const platform = await fetch(`/api/platforms/${params.id}.json`).then((response) => response.json());
	return { platform };
}
