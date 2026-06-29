export async function load({ fetch }) {
	const [stats, openapi] = await Promise.all([
		fetch('/api/v1/stats.json').then((r) => r.json()),
		fetch('/api/v1/openapi.json').then((r) => r.json()
		)
	]);
	return { stats, openapi };
}
