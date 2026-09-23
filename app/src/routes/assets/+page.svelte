<script lang="ts">
	import { onMount } from 'svelte';
	import MultiSelect from '$lib/MultiSelect.svelte';
	import type { MultiSelectOption } from '$lib/MultiSelect.svelte';
	import Pager from '$lib/Pager.svelte';
	import { ListState, pageCount, pageSlice } from '$lib/listState.svelte';
	import { ASSET_PAGE_SIZE, type AssetSummary } from '$lib/assets';

	let { data } = $props();

	const list = new ListState();
	let selectedTags = $state<string[]>([]);
	let selectedCategories = $state<string[]>([]);

	// The prerendered page only carries the first page; the full list loads after mount.
	let allAssets = $state<AssetSummary[] | null>(null);
	let loadError = $state(false);

	onMount(() => {
		fetch('/api/v1/assets.json')
			.then((r) => r.json())
			.then((assets: AssetSummary[]) => (allAssets = assets))
			.catch(() => (loadError = true));
	});

	const tagOptions = $derived<MultiSelectOption[]>(
		data.tags.map((tag: string) => ({ value: tag, label: tag }))
	);

	const categoryOptions = $derived<MultiSelectOption[]>(
		data.categories.map((category: string) => ({
			value: category,
			label: category.charAt(0).toUpperCase() + category.slice(1)
		}))
	);

	const filtering = $derived(
		list.query.trim() !== '' || selectedTags.length > 0 || selectedCategories.length > 0
	);

	const filtered = $derived.by(() => {
		if (!allAssets) return data.firstPage;
		const q = list.query.trim().toLowerCase();
		return allAssets.filter((a) => {
			const matchesQuery =
				q === '' ||
				a.display_name.toLowerCase().includes(q) ||
				a.symbol.toLowerCase().includes(q) ||
				a.id.toLowerCase().includes(q);
			const matchesTag =
				selectedTags.length === 0 || selectedTags.every((t) => (a.tags ?? []).includes(t));
			const matchesCategory =
				selectedCategories.length === 0 || (!!a.category && selectedCategories.includes(a.category));
			return matchesQuery && matchesTag && matchesCategory;
		});
	});

	// Until the full list arrives only the unfiltered first page can be shown.
	const loading = $derived(!allAssets && (filtering || list.page > 1));
	const matchCount = $derived(allAssets ? filtered.length : data.total);
	const currentPage = $derived(Math.min(list.page, pageCount(matchCount, ASSET_PAGE_SIZE)));
	const cards = $derived(allAssets ? pageSlice(filtered, currentPage, ASSET_PAGE_SIZE) : filtered);
	const setPage = (p: number) => (list.page = p);
</script>

<svelte:head>
	<title>Assets — Tribulnation Catalogue</title>
</svelte:head>

<main>
	<div class="header">
		<div>
			<h1>Assets</h1>
			<p class="subtitle">{data.total} assets</p>
		</div>
		<div class="controls">
			<MultiSelect
				options={categoryOptions}
				bind:value={() => selectedCategories, (v) => ((selectedCategories = v), list.resetPage())}
				placeholder="Filter by category…"
			/>
			<MultiSelect
				options={tagOptions}
				bind:value={() => selectedTags, (v) => ((selectedTags = v), list.resetPage())}
				placeholder="Filter by tag…"
			/>
			<input
				type="search"
				placeholder="Search by name or symbol…"
				bind:value={list.query}
				oninput={list.resetPage}
				class="search"
			/>
		</div>
	</div>

	<Pager total={matchCount} size={ASSET_PAGE_SIZE} bind:page={() => currentPage, setPage} />

	{#if loadError}
		<p class="empty">Could not load assets. Try reloading the page.</p>
	{:else if loading}
		<p class="empty">Loading…</p>
	{:else if cards.length === 0}
		<p class="empty">No assets match the current filters</p>
	{:else}
		<ul class="grid">
			{#each cards as asset (asset.id)}
				<li>
					<a href={`/assets/${asset.id}`} class="asset-card">
						<div class="icon-wrap">
							{#if asset.icon}
								<img src={asset.icon} alt={asset.display_name} width="36" height="36" loading="lazy" decoding="async" />
							{:else}
								<div class="icon-placeholder">{asset.symbol?.charAt(0) ?? '?'}</div>
							{/if}
						</div>
						<div class="info">
							<span class="name">{asset.display_name}</span>
							<span class="symbol">{asset.symbol}</span>
						</div>
					</a>
				</li>
			{/each}
		</ul>
	{/if}

	<Pager total={matchCount} size={ASSET_PAGE_SIZE} bind:page={() => currentPage, setPage} scrollTop />
</main>

<style>
	main {
		max-width: 64rem;
		margin: 0 auto;
		padding: 2rem 1.5rem 4rem;
	}

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

	.controls {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		flex-wrap: wrap;
	}

	.search {
		background: #111116;
		border: 1px solid #2a2a38;
		border-radius: 6px;
		color: #e4e4eb;
		padding: 0.5rem 0.875rem;
		font-size: 0.875rem;
		width: 220px;
		outline: none;
		font-family: inherit;
	}

	.search::placeholder {
		color: #44445a;
	}

	.search:focus {
		border-color: #4f46e5;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 0.5rem;
		list-style: none;
	}

	.asset-card {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		background: #111116;
		border: 1px solid #1e1e26;
		border-radius: 8px;
		text-decoration: none;
		transition: border-color 0.12s, background 0.12s;
		min-width: 0;
	}

	.asset-card:hover {
		border-color: #3a3a58;
		background: #15151c;
		text-decoration: none;
	}

	.icon-wrap {
		flex-shrink: 0;
		width: 36px;
		height: 36px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.icon-wrap img {
		width: 36px;
		height: 36px;
		object-fit: contain;
		border-radius: 100%;
	}

	.icon-placeholder {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		background: #1e1e30;
		border: 1px solid #2a2a40;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.85rem;
		font-weight: 600;
		color: #6666a0;
	}

	.info {
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.name {
		font-size: 0.875rem;
		font-weight: 500;
		color: #e4e4eb;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.symbol {
		font-size: 0.75rem;
		color: #55556a;
		font-family: ui-monospace, 'Cascadia Code', monospace;
	}

	.empty {
		color: #55556a;
		padding: 3rem 0;
		text-align: center;
	}

	@media (max-width: 600px) {
		.controls {
			width: 100%;
		}

		.search {
			width: 100%;
		}
	}
</style>
