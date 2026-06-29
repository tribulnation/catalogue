<script>
	let { data } = $props();
</script>

<svelte:head>
	<title>Platforms | Tribulnation Catalogue API</title>
</svelte:head>

<main class="api-main">
	<h1>Platforms</h1>
	<p>
		<a href="/api/v1/platforms.json">All JSON</a>
		<a href="/api/v1/blockchains.json">Blockchains</a>
		<a href="/api/v1/cexs.json">CEXs</a>
		<a href="/api/v1/dexs.json">DEXs</a>
	</p>
	<ul>
		{#each data.platforms as platform}
			<li>
				<a href={`/api/v1/platforms/${platform.id}`}>{platform.display_name}</a>
				<span>{platform.kind}</span>
			</li>
		{/each}
	</ul>
</main>
