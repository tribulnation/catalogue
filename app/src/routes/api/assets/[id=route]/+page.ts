export async function load({ fetch, params }) {
	const asset = await fetch(`/api/assets/${params.id}.json`).then((response) => response.json());
	return { asset };
}
