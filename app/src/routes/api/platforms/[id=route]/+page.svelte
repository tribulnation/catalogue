<script>
	let { data } = $props();
</script>

<svelte:head>
	<title>{data.platform.display_name} | Platforms</title>
</svelte:head>

<main class="api-main">
	<p><a href="/api/platforms">Platforms</a></p>
	<h1>{data.platform.display_name}</h1>
	<p>{data.platform.kind}</p>
	<p><a href={`/api/v1/platforms/${data.platform.id}.json`}>Raw JSON</a></p>

	{#if data.platform.about?.en}
		<p>{data.platform.about.en}</p>
	{/if}
</main>
