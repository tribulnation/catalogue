<script lang="ts">
	import Copy from '$lib/Copy.svelte';

	let { data } = $props();
	const asset = $derived(data.asset);
	const locales = $derived(asset.about ? Object.keys(asset.about).sort() : []);

	const kindLabel: Record<string, string> = {
		spot: 'Spot',
		perpetual: 'Perpetual',
		debt: 'Debt',
		collateral: 'Collateral',
		pools: 'Liquidity Pools',
		pool: 'Liquidity Pools'
	};

	// The index uses 'pool' (singular) but the route uses 'pools'
	const kindUrl = (kind: string) => (kind === 'pool' ? 'pools' : kind);

	type InstrumentRef = { kind: string; platform: string; id: string; role: string };

	const instrumentsByKind = $derived(() => {
		const groups: Record<string, InstrumentRef[]> = {};
		for (const ref of data.instruments as InstrumentRef[]) {
			(groups[ref.kind] ??= []).push(ref);
		}
		return groups;
	});

	let iconCopied = $state(false);

	function copyIcon(path: string) {
		const url = new URL(path, window.location.href).href;
		navigator.clipboard.writeText(url);
		iconCopied = true;
		setTimeout(() => (iconCopied = false), 1500);
	}
</script>

<svelte:head>
	<title>{asset.display_name} ({asset.symbol}) — Assets</title>
</svelte:head>

<main>
	<nav class="breadcrumb">
		<a href="/assets">Assets</a>
		<span>/</span>
		<span>{asset.display_name}</span>
	</nav>

	<div class="header">
		<div class="icon-wrap">
			{#if asset.icon}
				<button class="icon-btn" onclick={() => copyIcon(asset.icon!)} title="Copy icon URL">
					<img src={asset.icon} alt={asset.display_name} width="56" height="56" />
					<span class="icon-copy-overlay" aria-hidden="true">
						{#if iconCopied}
							<svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">
								<path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 1 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/>
							</svg>
						{:else}
							<svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">
								<path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1z"/>
								<path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5H3.5A1.5 1.5 0 0 0 2 3h12a1.5 1.5 0 0 0-1.5-1.5H11A1.5 1.5 0 0 0 9.5 0h-3z"/>
							</svg>
						{/if}
					</span>
				</button>
			{:else}
				<div class="icon-placeholder">{asset.symbol?.charAt(0) ?? '?'}</div>
			{/if}
		</div>
		<div>
			<h1>{asset.display_name}</h1>
			<div class="meta">
				<code class="symbol">{asset.symbol}</code>
				{#if asset.tags}
					{#each asset.tags as tag}
						<span class="tag">{tag}</span>
					{/each}
				{/if}
			</div>
		</div>
	</div>

	{#if asset.about?.en}
		<section>
			<p class="about">{asset.about.en}</p>
		</section>
	{/if}

	<div class="details">
		{#if asset.pegged_to}
			<div class="detail-row">
				<span class="detail-label">Pegged to</span>
				<a href={`/assets/${asset.pegged_to.asset}`} class="detail-value">
					{asset.pegged_to.asset}
				</a>
			</div>
		{/if}

		{#if asset.urls && Object.keys(asset.urls).length > 0}
			<div class="detail-row">
				<span class="detail-label">Links</span>
				<span class="detail-value links">
					{#each Object.entries(asset.urls) as [label, url]}
						<a href={url} target="_blank" rel="noopener noreferrer">{label}</a>
					{/each}
				</span>
			</div>
		{/if}

		{#if asset.external}
			{#each Object.entries(asset.external) as [provider, id]}
				<div class="detail-row">
					<span class="detail-label">{provider}</span>
					<Copy value={id} />
				</div>
			{/each}
		{/if}

		<div class="detail-row">
			<span class="detail-label">ID</span>
			<Copy value={asset.id} />
		</div>
	</div>

	{#if data.instruments.length > 0}
		<div class="instruments">
			<h2>Instruments</h2>
			{#each Object.entries(instrumentsByKind()) as [kind, refs]}
				<div class="instrument-group">
					<a href={`/instruments/${kindUrl(kind)}`} class="instrument-kind">{kindLabel[kind] ?? kind}</a>
					<ul class="instrument-list">
						{#each refs as ref}
							<li>
								<code class="inst-id">{ref.id}</code>
								<a href={`/platforms/${ref.platform}`} class="inst-platform">{ref.platform}</a>
								<span class="inst-role">{ref.role}</span>
							</li>
						{/each}
					</ul>
				</div>
			{/each}
		</div>
	{/if}

	{#if locales.length > 0}
		<div class="api-links">
			<span class="api-links-label">JSON</span>
			<a href={`/api/assets/${asset.id}.json`}>full</a>
			{#each locales as locale}
				<a href={`/api/assets/${asset.id}/${locale}.json`}>{locale}</a>
			{/each}
		</div>
	{/if}
</main>

<style>
	main {
		max-width: 48rem;
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

	.breadcrumb span:last-child {
		color: #8888a0;
	}

	.header {
		display: flex;
		align-items: center;
		gap: 1.25rem;
		margin-bottom: 1.75rem;
	}

	.icon-wrap {
		flex-shrink: 0;
	}

	.icon-btn {
		position: relative;
		display: block;
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
		border-radius: 100%;
	}

	.icon-btn img {
		width: 56px;
		height: 56px;
		object-fit: contain;
		border-radius: 100%;
		display: block;
	}

	.icon-copy-overlay {
		position: absolute;
		inset: 0;
		border-radius: 100%;
		background: rgba(0, 0, 0, 0.55);
		display: flex;
		align-items: center;
		justify-content: center;
		color: #fff;
		opacity: 0;
		transition: opacity 0.15s;
	}

	.icon-btn:hover .icon-copy-overlay {
		opacity: 1;
	}

	.icon-placeholder {
		width: 56px;
		height: 56px;
		border-radius: 50%;
		background: #1e1e30;
		border: 1px solid #2a2a40;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.25rem;
		font-weight: 700;
		color: #6666a0;
	}

	h1 {
		font-size: 1.75rem;
		font-weight: 700;
		color: #fff;
		letter-spacing: -0.025em;
	}

	.meta {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-top: 0.3rem;
		flex-wrap: wrap;
	}

	.symbol {
		font-family: ui-monospace, 'Cascadia Code', monospace;
		font-size: 0.875rem;
		color: #7a7a94;
		background: #1a1a24;
		padding: 0.15rem 0.4rem;
		border-radius: 4px;
		border: 1px solid #2a2a38;
	}

	.tag {
		font-size: 0.72rem;
		padding: 0.15rem 0.5rem;
		border-radius: 999px;
		background: #1e1e2e;
		border: 1px solid #2a2a42;
		color: #8888b0;
		letter-spacing: 0.01em;
	}

	.about {
		color: #a8a8c0;
		line-height: 1.7;
		font-size: 0.9375rem;
		border-left: 2px solid #2a2a40;
		padding-left: 1rem;
		margin-bottom: 1.5rem;
	}

	.details {
		border: 1px solid #1e1e26;
		border-radius: 8px;
		overflow: hidden;
		margin-bottom: 1.5rem;
	}

	.detail-row {
		display: flex;
		align-items: baseline;
		gap: 1rem;
		padding: 0.7rem 1rem;
		border-bottom: 1px solid #1a1a22;
	}

	.detail-row:last-child {
		border-bottom: none;
	}

	.detail-label {
		font-size: 0.8rem;
		color: #55556a;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		width: 7rem;
		flex-shrink: 0;
	}

	.detail-value {
		font-size: 0.9rem;
		color: #c0c0d8;
	}

	.detail-value.mono {
		font-family: ui-monospace, 'Cascadia Code', monospace;
		font-size: 0.85rem;
		color: #8888a8;
	}

	.detail-value.links {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.api-links {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-size: 0.8rem;
	}

	.api-links-label {
		color: #44445a;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-size: 0.72rem;
	}

	.instruments {
		margin-bottom: 1.5rem;
	}

	.instruments h2 {
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #44445a;
		margin-bottom: 0.75rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid #1a1a22;
	}

	.instrument-group {
		margin-bottom: 0.75rem;
	}

	.instrument-kind {
		font-size: 0.8rem;
		font-weight: 600;
		color: #7a7a94;
		text-decoration: none;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		display: block;
		margin-bottom: 0.3rem;
	}

	.instrument-kind:hover { color: #a5a3ff; }

	.instrument-list {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.instrument-list li {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.3rem 0.75rem;
		background: #111116;
		border: 1px solid #1a1a22;
		border-radius: 6px;
		font-size: 0.8rem;
	}

	.inst-id {
		font-family: ui-monospace, 'Cascadia Code', monospace;
		color: #c0c0d8;
		flex: 1;
	}

	.inst-platform {
		color: #55556a;
		font-family: ui-monospace, 'Cascadia Code', monospace;
	}

	.inst-role {
		color: #3a3a58;
		font-size: 0.72rem;
	}
</style>
