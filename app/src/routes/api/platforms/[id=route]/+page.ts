export async function load({ fetch, params }) {
	const platform = await fetch(`/api/v1/platforms/${params.id}.json`).then((response) => response.json());
	return { platform };
}
