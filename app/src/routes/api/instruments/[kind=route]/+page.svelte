<script>
	let { data } = $props();
</script>

<svelte:head>
	<title>{data.kind} instruments | Instruments</title>
</svelte:head>

<main class="api-main">
	<p><a href="/api/v1/instruments">Instruments</a></p>
	<h1>{data.kind} instruments</h1>
	<p><a href={`/api/v1/instruments/${data.kind}.json`}>Raw JSON</a></p>
	<ul>
		{#each data.platforms as item}
			<li>
				<a href={`/api/v1/instruments/${data.kind}/${item.platform}.json`}>{item.platform}</a>
				<span>{item.count}</span>
			</li>
		{/each}
	</ul>
</main>
