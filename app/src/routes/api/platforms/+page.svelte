<script>
	let { data } = $props();
</script>

<svelte:head>
	<title>Platforms | Tribulnation Catalogue API</title>
</svelte:head>

<main class="api-main">
	<h1>Platforms</h1>
	<p>
		<a href="/api/platforms.json">All JSON</a>
		<a href="/api/platforms/blockchains.json">Blockchains</a>
		<a href="/api/platforms/cexs.json">CEXs</a>
		<a href="/api/platforms/dexs.json">DEXs</a>
	</p>
	<ul>
		{#each data.platforms as platform}
			<li>
				<a href={`/api/platforms/${platform.id}`}>{platform.display_name}</a>
				<span>{platform.kind}</span>
			</li>
		{/each}
	</ul>
</main>
