export async function load({ fetch }) {
	const assets = await fetch('/api/assets.json').then((response) => response.json());
	return { assets };
}
