<script>
	let { data } = $props();

	function locales(asset) {
		return asset.about ? Object.keys(asset.about).sort() : [];
	}
</script>

<svelte:head>
	<title>{data.asset.display_name} | Assets</title>
</svelte:head>

<main class="api-main">
	<p><a href="/api/assets">Assets</a></p>
	<h1>{data.asset.display_name}</h1>
	<p>{data.asset.symbol}</p>

	<ul>
		<li><a href={`/api/assets/${data.asset.id}.json`}>Raw JSON</a></li>
		{#each locales(data.asset) as locale}
			<li><a href={`/api/assets/${data.asset.id}/${locale}.json`}>{locale} JSON</a></li>
		{/each}
	</ul>

	{#if data.asset.about?.en}
		<p>{data.asset.about.en}</p>
	{/if}
</main>
