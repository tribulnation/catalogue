export async function load({ fetch }) {
	const assets: { id: string; display_name: string; symbol: string }[] = await fetch(
		'/api/v1/assets.json'
	).then((response) => response.json());
	return { assets: assets.map(({ id, display_name, symbol }) => ({ id, display_name, symbol })) };
}
