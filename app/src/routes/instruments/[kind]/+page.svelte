<script lang="ts">
	let { data } = $props();

	const kindMeta: Record<string, { label: string }> = {
		spot: { label: 'Spot' },
		perpetual: { label: 'Perpetual' },
		debt: { label: 'Debt' },
		collateral: { label: 'Collateral' },
		pools: { label: 'Liquidity Pools' }
	};

	const meta = $derived(kindMeta[data.kind] ?? { label: data.kind });
	const total = $derived(data.platforms.reduce((s: number, p: { count: number }) => s + p.count, 0));

	let query = $state('');

	type Instrument = Record<string, unknown>;

	const allInstruments = $derived(
		data.instruments.flatMap(({ platform, data: items }: { platform: string; data: Record<string, Instrument> }) =>
			Object.values(items).map((inst) => ({ ...inst, _platform: platform }))
		)
	);

	const filtered = $derived(
		query.trim() === ''
			? allInstruments
			: allInstruments.filter((inst) => {
					const q = query.toLowerCase();
					return JSON.stringify(inst).toLowerCase().includes(q);
				})
	);
</script>

<svelte:head>
	<title>{meta.label} Instruments — Tribulnation Catalogue</title>
</svelte:head>

<main>
	<nav class="breadcrumb">
		<a href="/instruments">Instruments</a>
		<span>/</span>
		<span>{meta.label}</span>
	</nav>

	<div class="header">
		<div>
			<h1>{meta.label}</h1>
			<p class="subtitle">{total} instruments across {data.platforms.length} {data.platforms.length === 1 ? 'platform' : 'platforms'}</p>
		</div>
		<input
			type="search"
			placeholder="Filter…"
			bind:value={query}
			class="search"
		/>
	</div>

	{#if filtered.length === 0}
		<p class="empty">No instruments match "{query}"</p>
	{:else if data.kind === 'spot'}
		<table>
			<thead>
				<tr><th>ID</th><th>Base</th><th>Quote</th><th>Platform</th></tr>
			</thead>
			<tbody>
				{#each filtered as inst}
					<tr>
						<td class="mono">{inst.id}</td>
						<td><a href={`/assets/${inst.base}`}>{inst.base}</a></td>
						<td><a href={`/assets/${inst.quote}`}>{inst.quote}</a></td>
						<td class="mono dim"><a href={`/platforms/${inst._platform}`}>{inst._platform}</a></td>
					</tr>
				{/each}
			</tbody>
		</table>
	{:else if data.kind === 'perpetual'}
		<table>
			<thead>
				<tr><th>ID</th><th>Base</th><th>Quote</th><th>Settlement</th><th>Platform</th></tr>
			</thead>
			<tbody>
				{#each filtered as inst}
					<tr>
						<td class="mono">{inst.id}</td>
						<td><a href={`/assets/${inst.base}`}>{inst.base}</a></td>
						<td><a href={`/assets/${inst.quote}`}>{inst.quote}</a></td>
						<td><a href={`/assets/${inst.settlement}`}>{inst.settlement}</a></td>
						<td class="mono dim"><a href={`/platforms/${inst._platform}`}>{inst._platform}</a></td>
					</tr>
				{/each}
			</tbody>
		</table>
	{:else if data.kind === 'pools'}
		<table>
			<thead>
				<tr><th>Name</th><th>Assets</th><th>Platform</th></tr>
			</thead>
			<tbody>
				{#each filtered as inst}
					<tr>
						<td>{inst.name}</td>
						<td class="assets-cell">
							{#each inst.assets as asset}
								<a href={`/assets/${asset}`} class="asset-tag">{asset}</a>
							{/each}
						</td>
						<td class="mono dim"><a href={`/platforms/${inst._platform}`}>{inst._platform}</a></td>
					</tr>
				{/each}
			</tbody>
		</table>
	{:else}
		<!-- debt / collateral -->
		<table>
			<thead>
				<tr><th>Name</th><th>Asset</th><th>Platform</th></tr>
			</thead>
			<tbody>
				{#each filtered as inst}
					<tr>
						<td>{inst.name}</td>
						<td><a href={`/assets/${inst.asset}`}>{inst.asset}</a></td>
						<td class="mono dim"><a href={`/platforms/${inst._platform}`}>{inst._platform}</a></td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</main>

<style>
	main {
		max-width: 72rem;
		margin: 0 auto;
		padding: 2rem 1.5rem 4rem;
	}

	.breadcrumb {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.85rem;
		color: #55556a;
		margin-bottom: 2rem;
	}

	.breadcrumb span:last-child { color: #8888a0; }

	.header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1.75rem;
		flex-wrap: wrap;
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

	.search {
		background: #111116;
		border: 1px solid #2a2a38;
		border-radius: 6px;
		color: #e4e4eb;
		padding: 0.5rem 0.875rem;
		font-size: 0.875rem;
		width: 200px;
		outline: none;
		font-family: inherit;
	}

	.search::placeholder { color: #44445a; }
	.search:focus { border-color: #4f46e5; }

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}

	thead tr {
		border-bottom: 1px solid #1e1e26;
	}

	th {
		text-align: left;
		padding: 0.5rem 0.75rem;
		font-size: 0.72rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #44445a;
	}

	td {
		padding: 0.45rem 0.75rem;
		color: #c0c0d8;
		border-bottom: 1px solid #15151e;
	}

	tbody tr:hover td {
		background: #111118;
	}

	.mono {
		font-family: ui-monospace, 'Cascadia Code', monospace;
		font-size: 0.8rem;
	}

	.dim { color: #55556a; }

	.assets-cell {
		display: flex;
		flex-wrap: wrap;
		gap: 0.3rem;
	}

	.asset-tag {
		font-size: 0.75rem;
		padding: 0.1rem 0.4rem;
		background: #1a1a28;
		border: 1px solid #2a2a40;
		border-radius: 4px;
		color: #a5a3ff;
		text-decoration: none;
	}

	.asset-tag:hover { color: #c4c2ff; text-decoration: none; }

	.empty {
		color: #55556a;
		padding: 3rem 0;
		text-align: center;
	}

	@media (max-width: 640px) {
		.search {
			width: 100%;
		}

		table {
			display: block;
			overflow-x: auto;
			-webkit-overflow-scrolling: touch;
		}
	}
</style>
