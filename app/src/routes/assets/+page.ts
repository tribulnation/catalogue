export async function load({ fetch }) {
	const assets = await fetch('/api/assets.json').then((r) => r.json());
	return { assets };
}
