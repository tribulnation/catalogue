<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<nav>
	<a class="brand" href="/">
		<img src={favicon} alt="Tribulnation" width="28" height="28" class="brand-icon" />
		Catalogue
	</a>
	<div class="links">
		<a href="/">Home</a>
		<a href="/assets">Assets</a>
		<a href="/platforms">Platforms</a>
		<a href="/instruments">Instruments</a>
		<a href="/api" class="secondary">API</a>
	</div>
</nav>

{@render children()}

<style>
	:global(*) {
		box-sizing: border-box;
		margin: 0;
		padding: 0;
	}

	:global(body) {
		background: #0c0c0e;
		color: #e4e4eb;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
		font-size: 15px;
		line-height: 1.5;
		min-height: 100dvh;
	}

	:global(a) {
		color: #a5a3ff;
		text-decoration: none;
	}

	:global(a:hover) {
		color: #c4c2ff;
		text-decoration: underline;
	}

	nav {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 1.5rem;
		height: 52px;
		border-bottom: 1px solid #1e1e26;
		position: sticky;
		top: 0;
		background: #0c0c0e;
		z-index: 10;
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 600;
		font-size: 1rem;
		color: #e4e4eb;
		letter-spacing: -0.01em;
	}

	.brand-icon {
		border-radius: 6px;
		flex-shrink: 0;
	}

	.brand:hover {
		color: #fff;
		text-decoration: none;
	}

	.links {
		display: flex;
		gap: 1.5rem;
		align-items: center;
	}

	.links a {
		color: #8888a0;
		font-size: 0.9rem;
		font-weight: 500;
	}

	.links a:hover {
		color: #e4e4eb;
		text-decoration: none;
	}

	.links .secondary {
		color: #55556a;
	}
</style>
