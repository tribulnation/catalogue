export async function load({ fetch }) {
	const [stats, openapi] = await Promise.all([
		fetch('/api/stats.json').then((r) => r.json()),
		fetch('/api/openapi.json').then((r) => r.json()
		)
	]);
	return { stats, openapi };
}
