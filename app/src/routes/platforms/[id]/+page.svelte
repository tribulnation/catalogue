<script lang="ts">
	let { data } = $props();
	const platform = $derived(data.platform);

	const kindLabel: Record<string, string> = {
		blockchain: 'Blockchain',
		cex: 'Centralized Exchange',
		dex: 'Decentralized Exchange'
	};
</script>

<svelte:head>
	<title>{platform.display_name} — Platforms</title>
</svelte:head>

<main>
	<nav class="breadcrumb">
		<a href="/platforms">Platforms</a>
		<span>/</span>
		<span>{platform.display_name}</span>
	</nav>

	<div class="header">
		<div class="icon-wrap">
			{#if platform.icon}
				<img src={platform.icon} alt={platform.display_name} width="56" height="56" />
			{:else}
				<div class="icon-placeholder">{platform.display_name.charAt(0)}</div>
			{/if}
		</div>
		<div>
			<h1>{platform.display_name}</h1>
			<div class="meta">
				<span class="kind">{kindLabel[platform.kind] ?? platform.kind}</span>
				{#if platform.category}
					<span class="tag">{platform.category.toUpperCase()}</span>
				{/if}
			</div>
		</div>
	</div>

	{#if platform.about?.en}
		<section>
			<p class="about">{platform.about.en}</p>
		</section>
	{/if}

	<div class="details">
		{#if platform.native_asset}
			<div class="detail-row">
				<span class="detail-label">Native asset</span>
				<a href={`/assets/${platform.native_asset}`} class="detail-value">
					{platform.native_asset}
				</a>
			</div>
		{/if}

		{#if platform.namespace}
			<div class="detail-row">
				<span class="detail-label">Namespace</span>
				<code class="detail-value mono">{platform.namespace}</code>
			</div>
		{/if}

		{#if platform.chain_id !== undefined}
			<div class="detail-row">
				<span class="detail-label">Chain ID</span>
				<code class="detail-value mono">{platform.chain_id}</code>
			</div>
		{/if}

		{#if platform.urls && Object.keys(platform.urls).length > 0}
			<div class="detail-row">
				<span class="detail-label">Links</span>
				<span class="detail-value links">
					{#each Object.entries(platform.urls) as [label, url]}
						<a href={url as string} target="_blank" rel="noopener noreferrer">{label}</a>
					{/each}
				</span>
			</div>
		{/if}

		<div class="detail-row">
			<span class="detail-label">ID</span>
			<code class="detail-value mono">{platform.id}</code>
		</div>
	</div>

	<div class="api-links">
		<span class="api-links-label">JSON</span>
		<a href={`/api/platforms/${platform.id}.json`}>full</a>
	</div>
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

	.icon-wrap img {
		width: 56px;
		height: 56px;
		object-fit: contain;
		border-radius: 100%;
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

	.kind {
		font-size: 0.8rem;
		color: #7a7a94;
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
</style>
