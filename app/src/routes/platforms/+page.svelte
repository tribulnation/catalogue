<script lang="ts">
	let { data } = $props();

	const kindLabel: Record<string, string> = {
		blockchain: 'Blockchains',
		cex: 'Centralized Exchanges',
		dex: 'Decentralized Exchanges'
	};

	const kindOrder = ['blockchain', 'cex', 'dex'];

	const grouped = $derived(
		kindOrder
			.map((kind) => ({
				kind,
				label: kindLabel[kind] ?? kind,
				platforms: data.platforms.filter((p: { kind: string }) => p.kind === kind)
			}))
			.filter((g) => g.platforms.length > 0)
	);
</script>

<svelte:head>
	<title>Platforms — Tribulnation Catalogue</title>
</svelte:head>

<main>
	<div class="header">
		<h1>Platforms</h1>
		<p class="subtitle">{data.platforms.length} platforms</p>
	</div>

	{#each grouped as group}
		<section>
			<h2>{group.label}</h2>
			<ul class="grid">
				{#each group.platforms as platform}
					<li>
						<a href={`/platforms/${platform.id}`} class="platform-card">
							<div class="icon-wrap">
								{#if platform.icon}
									<img src={platform.icon} alt={platform.display_name} width="36" height="36" />
								{:else}
									<div class="icon-placeholder">{platform.display_name.charAt(0)}</div>
								{/if}
							</div>
							<span class="name">{platform.display_name}</span>
						</a>
					</li>
				{/each}
			</ul>
		</section>
	{/each}
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

	section {
		margin-bottom: 2.5rem;
	}

	h2 {
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #44445a;
		margin-bottom: 0.75rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid #1a1a22;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 0.5rem;
		list-style: none;
	}

	.platform-card {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		background: #111116;
		border: 1px solid #1e1e26;
		border-radius: 8px;
		text-decoration: none;
		transition: border-color 0.12s, background 0.12s;
	}

	.platform-card:hover {
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

	.name {
		font-size: 0.875rem;
		font-weight: 500;
		color: #e4e4eb;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
</style>
