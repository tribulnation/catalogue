<script lang="ts">
	import { pageCount } from '$lib/listState.svelte';

	let {
		total,
		size,
		page = $bindable(1),
		scrollTop = false
	}: {
		total: number;
		size: number;
		page?: number;
		/** Scroll back to the top of the page after changing page, for a pager below the list. */
		scrollTop?: boolean;
	} = $props();

	const pages = $derived(pageCount(total, size));
	const first = $derived(total === 0 ? 0 : (page - 1) * size + 1);
	const last = $derived(Math.min(page * size, total));

	function go(to: number) {
		page = Math.min(Math.max(1, to), pages);
		if (scrollTop) window.scrollTo({ top: 0 });
	}
</script>

{#if pages > 1}
	<nav class="pager" aria-label="Pagination">
		<span class="range"
			>{first.toLocaleString()}–{last.toLocaleString()} of {total.toLocaleString()}</span
		>
		<div class="buttons">
			<button onclick={() => go(1)} disabled={page <= 1} aria-label="First page">«</button>
			<button onclick={() => go(page - 1)} disabled={page <= 1} aria-label="Previous page">‹</button
			>
			<span class="current">Page {page} of {pages}</span>
			<button onclick={() => go(page + 1)} disabled={page >= pages} aria-label="Next page">›</button
			>
			<button onclick={() => go(pages)} disabled={page >= pages} aria-label="Last page">»</button>
		</div>
	</nav>
{/if}

<style>
	.pager {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		flex-wrap: wrap;
		margin: 1rem 0;
		font-size: 0.8rem;
		color: #55556a;
	}

	.buttons {
		display: flex;
		align-items: center;
		gap: 0.35rem;
	}

	.current {
		padding: 0 0.5rem;
		color: #8888a0;
	}

	button {
		background: #111116;
		border: 1px solid #2a2a38;
		border-radius: 6px;
		color: #c0c0d8;
		font: inherit;
		min-width: 2rem;
		padding: 0.3rem 0.5rem;
		cursor: pointer;
	}

	button:hover:not(:disabled) {
		border-color: #4f46e5;
	}

	button:disabled {
		opacity: 0.35;
		cursor: default;
	}
</style>
