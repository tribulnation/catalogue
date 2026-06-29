<script>
	let { data } = $props();
</script>

<svelte:head>
	<title>Assets | Tribulnation Catalogue API</title>
</svelte:head>

<main class="api-main">
	<h1>Assets</h1>
	<p><a href="/api/v1/assets.json">Raw JSON</a></p>
	<ul>
		{#each data.assets as asset}
			<li>
				<a href={`/api/assets/${asset.id}`}>{asset.display_name}</a>
				<span>{asset.symbol}</span>
			</li>
		{/each}
	</ul>
</main>
