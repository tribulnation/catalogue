const kinds = ['spot', 'perpetual', 'debt', 'pools'];

export const entries = () => kinds.map((kind) => ({ kind }));

export async function load({ fetch, params }) {
	const { kind } = params;
	const platforms: { platform: string; count: number }[] = await fetch(
		`/api/instruments/${kind}.json`
	).then((r) => r.json());

	const instruments = await Promise.all(
		platforms.map(({ platform }) =>
			fetch(`/api/instruments/${kind}/${platform}.json`)
				.then((r) => r.json())
				.then((data) => ({ platform, data }))
		)
	);

	return { kind, platforms, instruments };
}
