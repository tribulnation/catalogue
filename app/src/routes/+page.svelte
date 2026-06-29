<script lang="ts">
	import { onMount } from 'svelte';

	let stats = $state<Record<string, number> | null>(null);

	onMount(async () => {
		stats = await fetch('/api/v1/stats.json').then((r) => r.json());
	});
</script>

<svelte:head>
	<title>Tribulnation Catalogue</title>
</svelte:head>

<main>
	<div class="hero">
		<h1>Tribulnation Catalogue</h1>
		<p class="tagline">
			Open-source reference data for crypto assets, platforms, networks, translations, and
			instruments.
		</p>
		<div class="cta">
			<a href="/assets" class="btn primary">Browse Assets</a>
			<a href="/platforms" class="btn secondary">Browse Platforms</a>
		</div>
	</div>

	{#if stats}
		<div class="stats">
			<div class="stat">
				<span class="stat-value">{stats.assets}</span>
				<span class="stat-label">Assets</span>
			</div>
			<div class="stat">
				<span class="stat-value">{stats.assets_with_icons}</span>
				<span class="stat-label">With Icons</span>
			</div>
			<div class="stat">
				<span class="stat-value">{stats.platforms}</span>
				<span class="stat-label">Platforms</span>
			</div>
			<div class="stat">
				<span class="stat-value">{stats.blockchains}</span>
				<span class="stat-label">Blockchains</span>
			</div>
			<div class="stat">
				<span class="stat-value">{stats.cexs}</span>
				<span class="stat-label">CEXs</span>
			</div>
			<div class="stat">
				<span class="stat-value">{stats.asset_translations}</span>
				<span class="stat-label">Asset Translations</span>
			</div>
		</div>
	{/if}

	<div class="sections">
		<a href="/assets" class="card">
			<div class="card-icon">
				<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
				</svg>
			</div>
			<div>
				<h2>Assets</h2>
				<p>Canonical metadata for crypto assets — symbols, icons, descriptions, external IDs, and pegs.</p>
			</div>
		</a>
		<a href="/platforms" class="card">
			<div class="card-icon">
				<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15a4.5 4.5 0 0 0 4.5 4.5H18a3.75 3.75 0 0 0 1.332-7.257 3 3 0 0 0-3.758-3.848 5.25 5.25 0 0 0-10.233 2.33A4.502 4.502 0 0 0 2.25 15Z" />
				</svg>
			</div>
			<div>
				<h2>Platforms</h2>
				<p>Blockchains, centralized and decentralized exchanges with chain IDs, namespaces, and more.</p>
			</div>
		</a>
	</div>

	<div class="api-link">
		<a href="/api">Browse the static JSON API →</a>
	</div>
</main>

<style>
	main {
		max-width: 56rem;
		margin: 0 auto;
		padding: 4rem 1.5rem 6rem;
	}

	.hero {
		text-align: center;
		padding: 3rem 0 2.5rem;
	}

	h1 {
		font-size: 2.5rem;
		font-weight: 700;
		letter-spacing: -0.03em;
		color: #fff;
		margin-bottom: 1rem;
	}

	.tagline {
		font-size: 1.1rem;
		color: #8888a0;
		max-width: 36rem;
		margin: 0 auto 2rem;
	}

	.cta {
		display: flex;
		gap: 0.75rem;
		justify-content: center;
	}

	.btn {
		display: inline-flex;
		align-items: center;
		padding: 0.6rem 1.25rem;
		border-radius: 6px;
		font-size: 0.9rem;
		font-weight: 500;
		text-decoration: none !important;
		transition: opacity 0.15s;
	}

	.btn:hover {
		opacity: 0.85;
	}

	.btn.primary {
		background: #4f46e5;
		color: #fff;
	}

	.btn.secondary {
		background: #1e1e26;
		color: #c0c0d0;
		border: 1px solid #2a2a38;
	}

	.stats {
		display: flex;
		flex-wrap: wrap;
		gap: 0;
		border: 1px solid #1e1e26;
		border-radius: 10px;
		margin: 2.5rem 0;
		overflow: hidden;
	}

	.stat {
		flex: 1;
		min-width: 120px;
		padding: 1.25rem 1.5rem;
		border-right: 1px solid #1e1e26;
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.stat:last-child {
		border-right: none;
	}

	.stat-value {
		font-size: 1.75rem;
		font-weight: 700;
		color: #fff;
		letter-spacing: -0.02em;
		font-variant-numeric: tabular-nums;
	}

	.stat-label {
		font-size: 0.78rem;
		color: #55556a;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.sections {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin: 2rem 0;
	}

	.card {
		display: flex;
		gap: 1rem;
		padding: 1.5rem;
		background: #111116;
		border: 1px solid #1e1e26;
		border-radius: 10px;
		color: #e4e4eb;
		text-decoration: none !important;
		transition: border-color 0.15s;
	}

	.card:hover {
		border-color: #3a3a58;
	}

	.card-icon {
		flex-shrink: 0;
		color: #4f46e5;
		margin-top: 0.1rem;
	}

	.card h2 {
		font-size: 1rem;
		font-weight: 600;
		color: #fff;
		margin-bottom: 0.3rem;
	}

	.card p {
		font-size: 0.875rem;
		color: #6666800;
		line-height: 1.5;
		color: #7777900;
		color: #7a7a94;
	}

	.api-link {
		text-align: center;
		margin-top: 3rem;
		color: #55556a;
		font-size: 0.875rem;
	}

	@media (max-width: 600px) {
		h1 { font-size: 1.75rem; }
		.sections { grid-template-columns: 1fr; }
		.stat { flex: 1 1 calc(33.33% - 2px); min-width: 0; padding: 1rem; }
		.stat-value { font-size: 1.4rem; }
	}
</style>
