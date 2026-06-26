<script lang="ts">
	let { data } = $props();

	const kindMeta: Record<string, { label: string; description: string }> = {
		spot: { label: 'Spot', description: 'Trading pairs' },
		perpetual: { label: 'Perpetual', description: 'Futures & perpetual contracts' },
		debt: { label: 'Debt', description: 'Lending debt tokens' },
		collateral: { label: 'Collateral', description: 'Lending collateral tokens' },
		pools: { label: 'Liquidity Pools', description: 'Decentralized liquidity pools' }
	};

	const total = $derived(
		data.indexes.reduce(
			(sum: number, idx: { platforms: { count: number }[] }) =>
				sum + idx.platforms.reduce((s: number, p: { count: number }) => s + p.count, 0),
			0
		)
	);
</script>

<svelte:head>
	<title>Instruments — Tribulnation Catalogue</title>
</svelte:head>

<main>
	<div class="header">
		<h1>Instruments</h1>
		<p class="subtitle">{total} instruments across {data.indexes.filter((i: { platforms: unknown[] }) => i.platforms.length > 0).length} types</p>
	</div>

	<div class="grid">
		{#each data.indexes as idx}
			{@const meta = kindMeta[idx.kind]}
			{#if idx.platforms.length > 0}
				<a href={`/instruments/${idx.kind}`} class="kind-card">
					<div class="kind-header">
						<span class="kind-label">{meta.label}</span>
						<span class="kind-total">{idx.platforms.reduce((s: number, p: { count: number }) => s + p.count, 0)}</span>
					</div>
					<p class="kind-desc">{meta.description}</p>
					<ul class="platform-list">
						{#each idx.platforms as p}
							<li>
								<span class="platform-name">{p.platform}</span>
								<span class="platform-count">{p.count}</span>
							</li>
						{/each}
					</ul>
				</a>
			{/if}
		{/each}
	</div>
</main>

<style>
	main {
		max-width: 64rem;
		margin: 0 auto;
		padding: 2rem 1.5rem 4rem;
	}

	.header {
		margin-bottom: 2rem;
	}

	h1 {
		font-size: 1.5rem;
		font-weight: 700;
		color: #fff;
		letter-spacing: -0.02em;
	}

	.subtitle {
		color: #55556a;
		font-size: 0.85rem;
		margin-top: 0.1rem;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		gap: 0.75rem;
	}

	.kind-card {
		display: block;
		padding: 1.25rem;
		background: #111116;
		border: 1px solid #1e1e26;
		border-radius: 10px;
		text-decoration: none;
		transition: border-color 0.12s, background 0.12s;
	}

	.kind-card:hover {
		border-color: #3a3a58;
		background: #15151c;
		text-decoration: none;
	}

	.kind-header {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		margin-bottom: 0.3rem;
	}

	.kind-label {
		font-size: 1rem;
		font-weight: 600;
		color: #fff;
	}

	.kind-total {
		font-size: 1.25rem;
		font-weight: 700;
		color: #4f46e5;
		font-variant-numeric: tabular-nums;
	}

	.kind-desc {
		font-size: 0.8rem;
		color: #55556a;
		margin-bottom: 1rem;
	}

	.platform-list {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.platform-list li {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.8rem;
	}

	.platform-name {
		color: #8888a0;
		font-family: ui-monospace, 'Cascadia Code', monospace;
	}

	.platform-count {
		color: #55556a;
		font-variant-numeric: tabular-nums;
	}
</style>
