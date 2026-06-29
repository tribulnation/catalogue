export async function load({ fetch, params }) {
	const asset = await fetch(`/api/v1/assets/${params.id}.json`).then((response) => response.json());
	return { asset };
}
