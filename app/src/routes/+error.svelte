<script>
	import { page } from '$app/stores';
</script>

<svelte:head>
	<title>{$page.status} — Tribulnation Catalogue</title>
</svelte:head>

<main>
	<span class="status">{$page.status}</span>
	<p>{$page.status === 404 ? 'Page not found.' : ($page.error?.message ?? 'Something went wrong.')}</p>
	<a href="/">← Home</a>
</main>

<style>
	main {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 60vh;
		gap: 1rem;
		text-align: center;
	}

	.status {
		font-size: 5rem;
		font-weight: 700;
		color: #1e1e2e;
		line-height: 1;
		letter-spacing: -0.02em;
	}

	p {
		color: #555;
		font-size: 0.95rem;
		margin: 0;
	}

	a {
		font-size: 0.85rem;
		color: #6e6bff;
		text-decoration: none;
		margin-top: 0.5rem;
	}

	a:hover {
		text-decoration: underline;
	}
</style>
