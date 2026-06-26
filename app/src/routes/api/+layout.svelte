<script lang="ts">
	let { children } = $props();
</script>

{@render children()}

<style>
	:global(.api-main) {
		max-width: 60rem;
		margin: 2rem auto;
		padding: 0 1.5rem 4rem;
		line-height: 1.6;
	}

	:global(.api-main h1) {
		font-size: 1.4rem;
		font-weight: 700;
		color: #fff;
		letter-spacing: -0.02em;
		margin-bottom: 1rem;
	}

	:global(.api-main h2) {
		font-size: 0.9rem;
		font-weight: 600;
		color: #8888a0;
		margin: 1.5rem 0 0.5rem;
	}

	:global(.api-main p) {
		color: #8888a0;
		margin-bottom: 0.75rem;
	}

	:global(.api-main p a) {
		margin-right: 0.75rem;
	}

	:global(.api-main ul) {
		list-style: none;
		padding: 0;
	}

	:global(.api-main li) {
		padding: 0.3rem 0;
		border-bottom: 1px solid #1a1a22;
		font-size: 0.9rem;
	}

	:global(.api-main li:last-child) {
		border-bottom: none;
	}

	:global(.api-main li span) {
		color: #55556a;
		margin-left: 0.5rem;
		font-family: ui-monospace, 'Cascadia Code', monospace;
		font-size: 0.8rem;
	}
</style>
