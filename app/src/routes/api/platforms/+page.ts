export async function load({ fetch }) {
	const platforms = await fetch('/api/platforms.json').then((response) => response.json());
	return { platforms };
}
