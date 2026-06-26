export async function load({ fetch }) {
	const platforms = await fetch('/api/platforms.json').then((r) => r.json());
	return { platforms };
}
