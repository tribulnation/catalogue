<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();

	let menuOpen = $state(false);

	function close() {
		menuOpen = false;
	}

	$effect(() => {
		document.body.style.overflow = menuOpen ? 'hidden' : '';
		return () => { document.body.style.overflow = ''; };
	});
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
		<a href="/market-data" class="secondary">Market Data</a>
		<a href="/api" class="secondary">API</a>
	</div>
</nav>

<!-- Mobile drawer overlay -->
<div
	class="drawer-overlay"
	class:open={menuOpen}
	onclick={close}
	role="presentation"
></div>

<!-- Mobile drawer -->
<aside class="drawer" class:open={menuOpen} aria-label="Navigation" inert={menuOpen ? undefined : true}>
	<div class="drawer-header">
		<a class="drawer-brand" href="/" onclick={close}>
			<img src={favicon} alt="Tribulnation" width="24" height="24" class="brand-icon" />
			Catalogue
		</a>
	</div>
	<nav class="drawer-nav">
		<a href="/" onclick={close}>Home</a>
		<a href="/assets" onclick={close}>Assets</a>
		<a href="/platforms" onclick={close}>Platforms</a>
		<a href="/instruments" onclick={close}>Instruments</a>
		<a href="/market-data" onclick={close} class="drawer-secondary">Market Data</a>
		<a href="/api" onclick={close} class="drawer-secondary">API</a>
	</nav>
	<div class="drawer-footer">
		<a href="https://tribulnation.com" target="_blank" rel="noopener noreferrer">tribulnation.com ↗</a>
		<a href="https://github.com/tribulnation/catalogue" target="_blank" rel="noopener noreferrer">GitHub ↗</a>
	</div>
</aside>

<!-- Mobile FAB -->
<button class="menu-fab" onclick={() => (menuOpen = !menuOpen)} aria-label={menuOpen ? 'Close menu' : 'Open menu'}>
	{#if menuOpen}
		<svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true">
			<line x1="3" y1="3" x2="15" y2="15"/>
			<line x1="15" y1="3" x2="3" y2="15"/>
		</svg>
	{:else}
		<svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true">
			<line x1="2" y1="4.5" x2="16" y2="4.5"/>
			<line x1="2" y1="9" x2="16" y2="9"/>
			<line x1="2" y1="13.5" x2="16" y2="13.5"/>
		</svg>
	{/if}
</button>

{@render children()}

<footer>
	<div class="foot-inner">
		<span class="foot-copy">© {new Date().getFullYear()} <a href="https://tribulnation.com">Tribulnation Labs</a> · Barcelona</span>
		<div class="foot-links">
			<a href="https://tribulnation.com" target="_blank" rel="noopener noreferrer">tribulnation.com ↗</a>
			<a href="https://github.com/tribulnation/catalogue" target="_blank" rel="noopener noreferrer">GitHub ↗</a>
			<a href="https://www.npmjs.com/package/@tribulnation/catalogue" target="_blank" rel="noopener noreferrer">npm ↗</a>
			<a href="https://pypi.org/project/tribulnation-catalogue/" target="_blank" rel="noopener noreferrer">PyPI ↗</a>
		</div>
	</div>
</footer>

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

	/* Drawer overlay */
	.drawer-overlay {
		display: none;
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.6);
		z-index: 40;
		opacity: 0;
		pointer-events: none;
		transition: opacity 0.25s;
		cursor: pointer;
	}

	.drawer-overlay.open {
		opacity: 1;
		pointer-events: auto;
	}

	/* Drawer */
	.drawer {
		display: none;
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100dvh;
		background: #0c0c0e;
		z-index: 50;
		flex-direction: column;
		transform: translateX(-100%);
		transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.drawer.open {
		transform: translateX(0);
	}

	.drawer-header {
		padding: 0 1.5rem;
		height: 52px;
		display: flex;
		align-items: center;
		border-bottom: 1px solid #1e1e26;
		flex-shrink: 0;
	}

	.drawer-brand {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 600;
		font-size: 1rem;
		color: #e4e4eb;
		letter-spacing: -0.01em;
		text-decoration: none;
	}

	.drawer-brand:hover {
		color: #fff;
		text-decoration: none;
	}

	.drawer-nav {
		display: flex;
		flex-direction: column;
		flex: 1;
		justify-content: center;
		padding: 1rem 0;
	}

	.drawer-nav a {
		padding: 0.55rem 1.75rem;
		font-size: 2.2rem;
		font-weight: 600;
		letter-spacing: -0.02em;
		color: #c0c0d8;
		text-decoration: none;
		transition: color 0.1s;
	}

	.drawer-nav a:hover,
	.drawer-nav a:active {
		background: #111118;
		color: #fff;
		text-decoration: none;
	}

	.drawer-secondary {
		color: #55556a !important;
	}

	.drawer-footer {
		padding: 1.25rem 1.75rem;
		border-top: 1px solid #1e1e26;
		display: flex;
		gap: 1.5rem;
	}

	.drawer-footer a {
		font-size: 0.85rem;
		color: #44445a;
	}

	.drawer-footer a:hover {
		color: #8888a0;
		text-decoration: none;
	}

	/* FAB */
	.menu-fab {
		display: none;
		position: fixed;
		bottom: 1.5rem;
		right: 1.5rem;
		width: 48px;
		height: 48px;
		border-radius: 50%;
		background: #4f46e5;
		border: none;
		cursor: pointer;
		z-index: 60;
		align-items: center;
		justify-content: center;
		color: #fff;
		box-shadow: 0 4px 20px rgba(79, 70, 229, 0.4);
		transition: background 0.15s, box-shadow 0.15s;
	}

	.menu-fab:hover {
		background: #4338ca;
		box-shadow: 0 6px 24px rgba(79, 70, 229, 0.5);
	}

	footer {
		margin-top: 4rem;
		padding: 2rem 1.5rem;
		border-top: 1px solid #1e1e26;
		font-size: 0.8rem;
		color: #55556a;
	}

	.foot-inner {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 1rem;
		max-width: 72rem;
		margin: 0 auto;
	}

	.foot-copy :global(a) {
		color: #55556a;
	}

	.foot-copy :global(a:hover) {
		color: #8888a0;
		text-decoration: none;
	}

	.foot-links {
		display: flex;
		gap: 1.25rem;
	}

	.foot-links a {
		color: #55556a;
		transition: color 0.15s;
	}

	.foot-links a:hover {
		color: #8888a0;
		text-decoration: none;
	}

	@media (max-width: 600px) {
		.links {
			display: none;
		}

		.drawer {
			display: flex;
		}

		.menu-fab {
			display: flex;
		}

		footer {
			margin-top: 2.5rem;
			padding-bottom: 5rem; /* clear the FAB */
		}
	}
</style>
