<script lang="ts">
	import { onMount } from 'svelte';
	import Pager from '$lib/Pager.svelte';
	import { ListState, pageCount, pageSlice } from '$lib/listState.svelte';
	import {
		fetchInstruments,
		INSTRUMENT_PAGE_SIZE,
		type Instrument,
		type SearchableInstrument
	} from '$lib/instruments';

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

	const list = new ListState();

	// The prerendered page only carries the first page; the full list loads after mount.
	let allInstruments = $state<SearchableInstrument[] | null>(null);
	let loadError = $state(false);

	onMount(() => {
		fetchInstruments(data.kind, data.platforms)
			.then((instruments) => (allInstruments = instruments))
			.catch(() => (loadError = true));
	});

	const filtered: Instrument[] = $derived.by(() => {
		const q = list.query.trim().toLowerCase();
		if (!allInstruments) return data.firstPage;
		return q === '' ? allInstruments : allInstruments.filter((inst) => inst._search.includes(q));
	});

	// Until the full list arrives only the unfiltered first page can be shown.
	const loading = $derived(!allInstruments && (list.query.trim() !== '' || list.page > 1));
	const matchCount = $derived(allInstruments ? filtered.length : total);
	const currentPage = $derived(Math.min(list.page, pageCount(matchCount, INSTRUMENT_PAGE_SIZE)));
	const rows = $derived(
		allInstruments ? pageSlice(filtered, currentPage, INSTRUMENT_PAGE_SIZE) : filtered
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
			bind:value={list.query}
			oninput={list.resetPage}
			class="search"
		/>
	</div>

	<Pager total={matchCount} size={INSTRUMENT_PAGE_SIZE} bind:page={() => currentPage, (p) => (list.page = p)} />

	{#if loadError}
		<p class="empty">Could not load instruments. Try reloading the page.</p>
	{:else if loading}
		<p class="empty">Loading…</p>
	{:else if rows.length === 0}
		<p class="empty">No instruments match "{list.query}"</p>
	{:else if data.kind === 'spot'}
		<table>
			<thead>
				<tr><th>ID</th><th>Base</th><th>Quote</th><th>Platform</th></tr>
			</thead>
			<tbody>
				{#each rows as inst}
					<tr>
						<td class="mono">
							{#if inst.url}<a href={inst.url} target="_blank" rel="noopener noreferrer">{inst.id}</a>{:else}{inst.id}{/if}
							{#if inst.delisted}<span class="delisted-badge">Delisted</span>{/if}
						</td>
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
				<tr><th>ID</th><th>Base</th><th>Quote</th><th>Settlement</th><th>Multiplier</th><th>Platform</th></tr>
			</thead>
			<tbody>
				{#each rows as inst}
					<tr>
						<td class="mono">
							{#if inst.url}<a href={inst.url} target="_blank" rel="noopener noreferrer">{inst.id}</a>{:else}{inst.id}{/if}
							{#if inst.delisted}<span class="delisted-badge">Delisted</span>{/if}
						</td>
						<td><a href={`/assets/${inst.base}`}>{inst.base}</a></td>
						<td><a href={`/assets/${inst.quote}`}>{inst.quote}</a></td>
						<td><a href={`/assets/${inst.settlement}`}>{inst.settlement}</a></td>
						<td class="mono">{inst.multiplier ?? '1'}</td>
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
				{#each rows as inst}
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
				{#each rows as inst}
					<tr>
						<td>{inst.name}</td>
						<td><a href={`/assets/${inst.asset}`}>{inst.asset}</a></td>
						<td class="mono dim"><a href={`/platforms/${inst._platform}`}>{inst._platform}</a></td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}

	<Pager total={matchCount} size={INSTRUMENT_PAGE_SIZE} bind:page={() => currentPage, (p) => (list.page = p)} scrollTop />
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
	.delisted-badge {
		display: inline-block;
		margin-left: 0.5rem;
		padding: 0.15rem 0.4rem;
		border: 1px solid #8d6d3f;
		border-radius: 999px;
		color: #e4b96a;
		font-family: sans-serif;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.02em;
		line-height: 1.2;
		vertical-align: middle;
	}

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
