export async function load({ fetch }) {
	const platforms = await fetch('/api/v1/platforms.json').then((r) => r.json());
	return { platforms };
}
