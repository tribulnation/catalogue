<script lang="ts">
	let { data } = $props();

	let query = $state('');

	const filtered = $derived(
		query.trim() === ''
			? data.assets
			: data.assets.filter((a: { display_name: string; symbol: string; id: string }) => {
					const q = query.toLowerCase();
					return (
						a.display_name.toLowerCase().includes(q) ||
						a.symbol.toLowerCase().includes(q) ||
						a.id.toLowerCase().includes(q)
					);
				})
	);
</script>

<svelte:head>
	<title>Assets — Tribulnation Catalogue</title>
</svelte:head>

<main>
	<div class="header">
		<div>
			<h1>Assets</h1>
			<p class="subtitle">{data.assets.length} assets</p>
		</div>
		<input
			type="search"
			placeholder="Search by name or symbol…"
			bind:value={query}
			class="search"
		/>
	</div>

	{#if filtered.length === 0}
		<p class="empty">No assets match "{query}"</p>
	{:else}
		<ul class="grid">
			{#each filtered as asset}
				<li>
					<a href={`/assets/${asset.id}`} class="asset-card">
						<div class="icon-wrap">
							{#if asset.icon}
								<img src={asset.icon} alt={asset.display_name} width="36" height="36" />
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

	.search {
		background: #111116;
		border: 1px solid #2a2a38;
		border-radius: 6px;
		color: #e4e4eb;
		padding: 0.5rem 0.875rem;
		font-size: 0.875rem;
		width: 240px;
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
		.search {
			width: 100%;
		}
	}
</style>
