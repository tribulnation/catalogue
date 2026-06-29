export async function load({ fetch }) {
	const assets = await fetch('/api/v1/assets.json').then((r) => r.json());
	return { assets };
}
