const kinds = ['spot', 'perpetual', 'debt', 'collateral', 'pools'] as const;

export async function load({ fetch }) {
	const indexes = await Promise.all(
		kinds.map((kind) =>
			fetch(`/api/instruments/${kind}.json`)
				.then((r) => r.json())
				.then((platforms) => ({ kind, platforms }))
		)
	);
	return { indexes };
}
