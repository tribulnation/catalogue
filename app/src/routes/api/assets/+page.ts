export async function load({ fetch }) {
	const assets = await fetch('/api/v1/assets.json').then((response) => response.json());
	return { assets };
}
