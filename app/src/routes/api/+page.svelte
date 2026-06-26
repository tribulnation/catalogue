<script>
	let { data } = $props();
	const s = $derived(data.stats);
</script>

<svelte:head>
	<title>Tribulnation Catalogue API</title>
</svelte:head>

<main class="api-main">
	<h1>Tribulnation Catalogue API</h1>
	<p>Static JSON API for crypto assets, platforms, translations, instruments, and spam addresses.</p>

	<ul>
		<li>
			<a href="/api/assets">{s.assets} assets</a>
			<span><a href="/api/assets.json">JSON</a></span>
		</li>
		<li>
			<a href="/api/platforms">{s.platforms} platforms</a>
			<span><a href="/api/platforms.json">JSON</a></span>
		</li>
		<li>
			<a href="/api/translations">{s.asset_translations} asset translations, {s.network_translations} network translations</a>
		</li>
		<li>
			<a href="/api/instruments">{s.spot_instruments} spot instruments, {s.perpetual_instruments} perpetual instruments</a>
		</li>
		<li><a href="/api/spam">{s.spam_addresses} spam addresses</a></li>
		<li><a href="/api/indexes">Indexes</a></li>
		<li><a href="/api/stats.json">Stats JSON</a></li>
	</ul>
</main>
