<script lang="ts">
	import CodeBlock from '$lib/CodeBlock.svelte';
	let { data } = $props();
	const blocks = $derived(data.blocks);
</script>

<svelte:head>
	<title>Market Data · Catalogue</title>
</svelte:head>

<main>
	<div class="page">
		<h1>Market Data</h1>
		<p class="intro">
			Fetch current prices, historical prices, and market caps for any catalogue asset — crypto,
			forex, commodities — via third-party providers. Configure one or more sources and
			<code>MarketData</code> handles routing, fallback, and retries automatically.
		</p>

		<section>
			<h2>Installation</h2>
			<CodeBlock {...blocks.install} />
		</section>

		<section>
			<h2>Quick start</h2>
			<CodeBlock {...blocks.quickstart} />
		</section>

		<section>
			<h2>Providers</h2>
			<p>Each provider reads its API key from the environment:</p>
			<div class="provider-table-wrap">
				<table class="provider-table">
					<thead>
						<tr>
							<th>Provider</th>
							<th>Source</th>
							<th>Env var</th>
							<th>Covers</th>
						</tr>
					</thead>
					<tbody>
						<tr>
							<td>CoinGecko</td>
							<td><code>'coingecko'</code></td>
							<td><code>COINGECKO_PRO_API_KEY</code><br /><span class="or">or</span> <code>COINGECKO_DEMO_API_KEY</code></td>
							<td>Crypto — price, market cap, history</td>
						</tr>
						<tr>
							<td>CoinMarketCap</td>
							<td><code>'coinmarketcap'</code></td>
							<td><code>COINMARKETCAP_API_KEY</code></td>
							<td>Crypto — price, market cap, history</td>
						</tr>
						<tr>
							<td>Twelve Data</td>
							<td><code>'twelvedata'</code></td>
							<td><code>TWELVEDATA_API_KEY</code></td>
							<td>Precious metals (XAU, XAG†), forex</td>
						</tr>
						<tr>
							<td>Alpha Vantage</td>
							<td><code>'alphavantage'</code></td>
							<td><code>ALPHAVANTAGE_API_KEY</code></td>
							<td>Energy &amp; agricultural commodities (WTI, BRENT, …), forex</td>
						</tr>
					</tbody>
				</table>
			</div>
			<p class="footnote">† XAG requires a paid Twelve Data plan.</p>
		</section>

		<section>
			<h2>Retry &amp; logging</h2>
			<p>
				Retries on network errors and rate limits are on by default. Configure with
				<code>max_retries</code>, <code>base_delay</code>, and <code>max_delay</code>:
			</p>
			<CodeBlock {...blocks.retry} />
			<p>
				Provider errors are logged via Python's standard <code>logging</code> module. Pass
				<code>logger=None</code> to silence them:
			</p>
			<CodeBlock {...blocks.logger} />
		</section>

		<section>
			<h2>External IDs</h2>
			<p>
				Each asset carries external IDs that map to provider-specific symbols. These are used
				automatically by <code>MarketData</code> to route requests to the right provider.
			</p>
			<CodeBlock {...blocks.externalIds} />
			<p>
				Browse the <a href="/assets">asset catalogue</a> to see which external IDs each asset
				carries.
			</p>
		</section>
	</div>
</main>

<style>
	main {
		max-width: 56rem;
		margin: 0 auto;
		padding: 2.5rem 1.5rem;
	}

	.page {
		display: flex;
		flex-direction: column;
		gap: 2.5rem;
	}

	h1 {
		font-size: 1.75rem;
		font-weight: 700;
		letter-spacing: -0.03em;
		color: #e4e4eb;
	}

	h2 {
		font-size: 1rem;
		font-weight: 600;
		color: #e4e4eb;
		margin-bottom: 0.75rem;
		letter-spacing: -0.01em;
	}

	.intro {
		font-size: 0.95rem;
		color: #8888a0;
		line-height: 1.6;
		margin-top: -1rem;
	}

	section {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	p {
		font-size: 0.9rem;
		color: #8888a0;
		line-height: 1.6;
	}

	p code,
	.intro code {
		font-family: ui-monospace, 'Cascadia Code', monospace;
		font-size: 0.82rem;
		color: #a5a3ff;
		background: #16162a;
		padding: 0.1em 0.35em;
		border-radius: 3px;
	}

	.provider-table-wrap {
		overflow-x: auto;
		-webkit-overflow-scrolling: touch;
		border-radius: 8px;
		border: 1px solid #1e1e2a;
	}

	.provider-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.85rem;
	}

	.provider-table th {
		text-align: left;
		padding: 0.6rem 1rem;
		background: #111118;
		color: #55556a;
		font-weight: 500;
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		border-bottom: 1px solid #1e1e2a;
		white-space: nowrap;
	}

	.provider-table td {
		padding: 0.7rem 1rem;
		border-bottom: 1px solid #1a1a24;
		color: #c0c0d8;
		vertical-align: top;
		line-height: 1.5;
	}

	.provider-table tr:last-child td {
		border-bottom: none;
	}

	.provider-table tr:hover td {
		background: #0f0f16;
	}

	.provider-table code {
		font-family: ui-monospace, 'Cascadia Code', monospace;
		font-size: 0.8rem;
		color: #a5a3ff;
		background: #16162a;
		padding: 0.1em 0.35em;
		border-radius: 3px;
	}

	.or {
		font-size: 0.75rem;
		color: #44445a;
	}

	.footnote {
		font-size: 0.8rem;
		color: #44445a;
	}

	a {
		color: #a5a3ff;
	}

	a:hover {
		color: #c4c2ff;
	}

	@media (max-width: 600px) {
		h1 {
			font-size: 1.4rem;
		}

		main {
			padding: 1.5rem 1rem;
		}
	}
</style>
