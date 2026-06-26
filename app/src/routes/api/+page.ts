export async function load({ fetch }) {
	const stats = await fetch('/api/stats.json').then((response) => response.json());
	return { stats };
}
