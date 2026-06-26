<script lang="ts">
	let { value }: { value: string } = $props();
	let copied = $state(false);

	function copy() {
		navigator.clipboard.writeText(value);
		copied = true;
		setTimeout(() => (copied = false), 1500);
	}
</script>

<button onclick={copy} class="copy" class:copied title={copied ? 'Copied!' : 'Copy'}>
	<code>{value}</code>
	{#if copied}
		<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
			<path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 1 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/>
		</svg>
	{:else}
		<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true" class="icon">
			<path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1z"/>
			<path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5H3.5A1.5 1.5 0 0 0 2 3h12a1.5 1.5 0 0 0-1.5-1.5H11A1.5 1.5 0 0 0 9.5 0h-3z"/>
		</svg>
	{/if}
</button>

<style>
	.copy {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		background: none;
		border: none;
		padding: 0.15rem 0.35rem;
		border-radius: 4px;
		cursor: pointer;
		color: inherit;
		transition: background 0.1s;
	}

	.copy:hover {
		background: #1a1a2a;
	}

	.copy code {
		font-family: ui-monospace, 'Cascadia Code', monospace;
		font-size: 0.85rem;
		color: #8888a8;
	}

	.icon {
		color: #3a3a58;
		opacity: 0;
		transition: opacity 0.15s;
		flex-shrink: 0;
	}

	:global(.detail-row:hover) .icon,
	.copy:focus-visible .icon {
		opacity: 1;
	}

	.copy.copied code {
		color: #5a9a5a;
	}

	.copy.copied svg {
		color: #5a9a5a;
		opacity: 1;
	}
</style>
