<script lang="ts">
	let { data } = $props();
	const s = $derived(data.stats);
	const spec = $derived(data.openapi);

	// ── Schema helpers ───────────────────────────────────────────────

	function deref(schema: any): any {
		if (schema?.$ref) {
			const parts = (schema.$ref as string).replace(/^#\//, '').split('/');
			return parts.reduce((o: any, k: string) => o?.[k], spec);
		}
		return schema;
	}

	function typeLabel(schema: any): string {
		if (!schema) return 'any';
		if (schema.$ref) return (schema.$ref as string).split('/').pop() ?? 'ref';
		if (schema.anyOf) {
			const nonNull = schema.anyOf.filter((t: any) => t.type !== 'null');
			const nullable = nonNull.length < schema.anyOf.length;
			const inner = nonNull.length === 1 ? typeLabel(nonNull[0]) : 'union';
			return nullable ? inner + '?' : inner;
		}
		if (schema.type === 'array') return typeLabel(schema.items) + '[]';
		if (schema.type === 'object' && schema.additionalProperties)
			return '{string: ' + typeLabel(schema.additionalProperties) + '}';
		if (schema.enum)
			return schema.enum.map((v: unknown) => JSON.stringify(v)).join(' | ');
		return schema.type ?? 'any';
	}

	type PropRow = { name: string; type: string; required: boolean; depth: number };

	function propRows(schema: any, depth = 0, max = 3): PropRow[] {
		if (depth >= max) return [];
		let s = deref(schema);
		if (s?.anyOf) {
			const nn = s.anyOf.filter((t: any) => t.type !== 'null');
			if (nn.length === 1) s = deref(nn[0]);
		}
		if (s?.type === 'array') s = deref(s.items);
		else if (s?.type === 'object' && s.additionalProperties && !s.properties)
			s = deref(s.additionalProperties);
		if (!s?.properties) return [];

		const req = new Set<string>(s.required ?? []);
		const rows: PropRow[] = [];
		for (const [name, ps] of Object.entries(s.properties as Record<string, any>)) {
			rows.push({ name, type: typeLabel(ps), required: req.has(name), depth });
			let inner = deref(ps);
			if (inner?.anyOf) {
				const nn = inner.anyOf.filter((t: any) => t.type !== 'null');
				if (nn.length === 1) inner = deref(nn[0]);
			}
			if (inner?.type === 'array') inner = deref(inner.items);
			if (inner?.properties) rows.push(...propRows(ps, depth + 1, max));
		}
		return rows;
	}

	// ── Route helpers ────────────────────────────────────────────────

	type Route = {
		method: string;
		path: string;
		description: string;
		schema: any;
		params: string[];
	};

	function routes(prefix: string): Route[] {
		const paths: [string, Record<string, any>][] = Object.entries(spec?.paths ?? {});
		return paths
			.filter(
				([p]) => p === prefix || p === prefix + '.json' || p.startsWith(prefix + '/')
			)
			.flatMap(([p, methods]) =>
				Object.entries(methods).map(([method, op]) => ({
					method: method.toUpperCase(),
					path: p,
					description: op.description || op.summary || '',
					schema: op.responses?.['200']?.content?.['application/json']?.schema ?? null,
					params: [...p.matchAll(/\{([^}]+)\}/g)].map(([, n]) => n)
				}))
			);
	}

	// ── Try it ───────────────────────────────────────────────────────

	const EXAMPLES: Record<string, Record<string, string>> = {
		'/api/assets/{id}.json': { id: 'bitcoin' },
		'/api/assets/{id}/{locale}.json': { id: 'bitcoin', locale: 'en' },
		'/api/platforms/{id}.json': { id: 'ethereum' },
		'/api/platforms/{id}/{locale}.json': { id: 'ethereum', locale: 'en' },
		'/api/translations/assets/{platform}.json': { platform: 'arbitrum' },
		'/api/translations/networks/{platform}.json': { platform: 'arbitrum' },
		'/api/instruments/spot/{platform}.json': { platform: 'mexc' },
		'/api/instruments/perpetual/{platform}.json': { platform: 'dydx' },
		'/api/instruments/debt/{platform}.json': { platform: 'ethereum' },
		'/api/instruments/collateral/{platform}.json': { platform: 'ethereum' },
		'/api/instruments/pools/{platform}.json': { platform: 'ethereum' },
		'/api/instruments/index/{asset}.json': { asset: 'aave' },
		'/api/spam/{platform}.json': { platform: 'arbitrum' },
		'/api/indexes/external/{provider}.json': { provider: 'coingecko' }
	};

	function initialParams(): Record<string, string> {
		const out: Record<string, string> = {};
		for (const [path, params] of Object.entries(EXAMPLES)) {
			for (const [param, value] of Object.entries(params)) {
				out[`${path}:${param}`] = value;
			}
		}
		return out;
	}

	let paramValues = $state<Record<string, string>>(initialParams());

	function tryUrl(path: string, params: string[]): string {
		let url = path;
		for (const name of params) {
			url = url.replace(`{${name}}`, encodeURIComponent(paramValues[`${path}:${name}`] ?? ''));
		}
		return url;
	}

	function isReady(route: Route): boolean {
		return (
			route.params.length === 0 ||
			route.params.every((p) => paramValues[`${route.path}:${p}`]?.trim())
		);
	}

	// ── Sections ─────────────────────────────────────────────────────

	const sections = $derived([
		{
			label: 'Assets',
			stat: `${s.assets} assets`,
			browse: '/api/assets',
			prefix: '/api/assets'
		},
		{
			label: 'Platforms',
			stat: `${s.platforms} platforms (${s.blockchains} blockchains, ${s.cexs} CEX, ${s.dexs} DEX)`,
			browse: '/api/platforms',
			prefix: '/api/platforms'
		},
		{
			label: 'Translations',
			stat: `${s.asset_translations} asset · ${s.network_translations} network`,
			browse: '/api/translations',
			prefix: '/api/translations'
		},
		{
			label: 'Instruments',
			stat: `${s.spot_instruments} spot · ${s.perpetual_instruments} perpetual`,
			browse: '/api/instruments',
			prefix: '/api/instruments'
		},
		{
			label: 'Spam',
			stat: `${s.spam_addresses} addresses`,
			browse: '/api/spam',
			prefix: '/api/spam'
		},
		{
			label: 'Indexes',
			stat: '',
			browse: '/api/indexes',
			prefix: '/api/indexes'
		},
		{
			label: 'Stats',
			stat: '',
			browse: null,
			prefix: '/api/stats'
		}
	]);
</script>

<svelte:head>
	<title>Tribulnation Catalogue API</title>
</svelte:head>

<main class="api-main">
	<h1>Tribulnation Catalogue API</h1>
	<p>Static JSON API for crypto assets, platforms, translations, instruments, and spam addresses.</p>

	{#each sections as section}
		{@const sectionRoutes = routes(section.prefix)}
		<section class="api-section">
			<header>
				<span class="section-label">
					{#if section.browse}
						<a href={section.browse}>{section.label}</a>
					{:else}
						{section.label}
					{/if}
				</span>
				{#if section.stat}
					<span class="section-stat">{section.stat}</span>
				{/if}
			</header>

			{#if sectionRoutes.length > 0}
				<div class="route-list">
					{#each sectionRoutes as route}
						{@const rows = propRows(route.schema)}
						<details class="route-item">
							<summary class="route-row">
								<span class="method">{route.method}</span>
								<code class="route-path">{route.path}</code>
								<span class="route-desc">{route.description}</span>
								<span class="toggle">▾</span>
							</summary>

							<div class="expanded-panel">
								{#if route.schema}
									<div class="schema-panel">
										<span class="schema-type">{typeLabel(route.schema)}</span>
										{#if rows.length > 0}
											<div class="prop-list">
												{#each rows as row}
													<div class="prop-row" style:padding-left="{row.depth * 1.1}rem">
														<span class="prop-name">{row.name}</span>
														<span class="prop-type" class:opt={!row.required}>{row.type}</span>
													</div>
												{/each}
											</div>
										{/if}
									</div>
								{/if}

								<div class="try-panel">
									<span class="try-label">Try it</span>
									{#each route.params as param}
										<label class="param-field">
											<span class="param-name">{param}</span>
											<input
												class="param-input"
												type="text"
												placeholder={param}
												value={paramValues[`${route.path}:${param}`] ?? ''}
												oninput={(e) => {
													paramValues[`${route.path}:${param}`] = e.currentTarget.value;
												}}
											/>
										</label>
									{/each}
									<button
										type="button"
										class="try-btn"
										disabled={!isReady(route)}
										onclick={() => window.open(tryUrl(route.path, route.params), '_blank', 'noopener')}
									>Open ↗</button>
								</div>
							</div>
						</details>
					{/each}
				</div>
			{/if}
		</section>
	{/each}

	<section class="api-section">
		<header>
			<span class="section-label">OpenAPI</span>
			<span class="section-stat">machine-readable spec</span>
		</header>
		<div class="route-list">
			<details class="route-item">
				<summary class="route-row">
					<span class="method">GET</span>
					<code class="route-path">/api/openapi.json</code>
					<span class="route-desc">OpenAPI 3.x specification for this API.</span>
					<span class="toggle">▾</span>
				</summary>
				<div class="expanded-panel">
					<div class="try-panel">
						<span class="try-label">Try it</span>
						<button
							type="button"
							class="try-btn"
							onclick={() => window.open('/api/openapi.json', '_blank', 'noopener')}
						>Open ↗</button>
					</div>
				</div>
			</details>
		</div>
	</section>
</main>

<style>
	h1 {
		font-size: 1.4rem;
		font-weight: 600;
		margin: 0 0 0.5rem;
	}

	p {
		color: #888;
		margin: 0 0 2rem;
		font-size: 0.9rem;
	}

	.api-section {
		border-top: 1px solid #1e1e24;
		padding: 1.25rem 0;
	}

	header {
		display: flex;
		align-items: baseline;
		gap: 0.75rem;
		margin-bottom: 0.75rem;
	}

	.section-label {
		font-weight: 600;
		font-size: 0.85rem;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: #c4c2ff;
	}

	.section-label a {
		color: inherit;
		text-decoration: none;
	}

	.section-label a:hover {
		text-decoration: underline;
	}

	.section-stat {
		font-size: 0.8rem;
		color: #555;
	}

	/* ── Route list ─────────────────────── */

	.route-list {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
	}

	.route-item {
		border-radius: 4px;
	}

	.route-row {
		display: grid;
		grid-template-columns: 2.5rem minmax(0, max-content) 1fr auto;
		align-items: baseline;
		gap: 0.75rem;
		font-size: 0.82rem;
		padding: 0.3rem 0.4rem;
		border-radius: 4px;
		cursor: pointer;
		list-style: none;
		user-select: none;
	}

	.route-row::-webkit-details-marker {
		display: none;
	}

	.route-row:hover {
		background: #13131a;
	}

	.method {
		font-size: 0.65rem;
		font-weight: 700;
		color: #6e6bff;
		letter-spacing: 0.05em;
	}

	.route-path {
		font-family: 'SF Mono', 'Fira Mono', monospace;
		font-size: 0.8rem;
		color: #c4c2ff;
		background: none;
		padding: 0;
		white-space: nowrap;
	}

	.route-desc {
		color: #555;
	}

	.toggle {
		color: #444;
		font-size: 0.75rem;
		display: inline-block;
		transition: transform 0.15s;
		line-height: 1;
	}

	details[open] .toggle {
		transform: rotate(180deg);
	}

	/* ── Expanded panel ──────────────────── */

	.expanded-panel {
		margin: 0.1rem 0.4rem 0.5rem calc(2.5rem + 0.75rem + 0.4rem);
		display: flex;
		flex-direction: column;
		gap: 0;
		border-left: 2px solid #1e1e24;
	}

	/* ── Schema ──────────────────────────── */

	.schema-panel {
		padding: 0.6rem 0.75rem 0.6rem 0.75rem;
	}

	.schema-type {
		font-family: 'SF Mono', 'Fira Mono', monospace;
		font-size: 0.75rem;
		color: #888;
		display: block;
		margin-bottom: 0.5rem;
	}

	.prop-list {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
	}

	.prop-row {
		display: grid;
		grid-template-columns: 12rem 1fr;
		gap: 0.75rem;
		font-size: 0.77rem;
		font-family: 'SF Mono', 'Fira Mono', monospace;
	}

	.prop-name {
		color: #a8a6e8;
	}

	.prop-type {
		color: #666;
	}

	.prop-type.opt {
		color: #3e3e52;
	}

	/* ── Try it ──────────────────────────── */

	.try-panel {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-wrap: wrap;
		padding: 0.55rem 0.75rem;
		border-top: 1px solid #1a1a22;
	}

	.try-label {
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: #3a3a50;
		flex-shrink: 0;
	}

	.param-field {
		display: flex;
		align-items: center;
		gap: 0.35rem;
	}

	.param-name {
		font-family: 'SF Mono', 'Fira Mono', monospace;
		font-size: 0.72rem;
		color: #555;
	}

	.param-input {
		background: #0d0d14;
		border: 1px solid #252530;
		border-radius: 3px;
		color: #c4c2ff;
		font-family: 'SF Mono', 'Fira Mono', monospace;
		font-size: 0.75rem;
		padding: 0.2rem 0.45rem;
		width: 9rem;
		outline: none;
	}

	.param-input:focus {
		border-color: #4a48a0;
	}

	.try-btn {
		font-size: 0.75rem;
		font-family: 'SF Mono', 'Fira Mono', monospace;
		color: #6e6bff;
		background: none;
		padding: 0.2rem 0.55rem;
		border: 1px solid #2a2840;
		border-radius: 3px;
		cursor: pointer;
		transition: background 0.1s;
	}

	.try-btn:hover:not(:disabled) {
		background: #13131a;
	}

	.try-btn:disabled {
		color: #333;
		border-color: #1e1e24;
		cursor: default;
	}
</style>
