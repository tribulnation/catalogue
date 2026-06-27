<script lang="ts">
	let { html, code }: { html: string; code: string } = $props();
	let copied = $state(false);

	function copy() {
		navigator.clipboard.writeText(code);
		copied = true;
		setTimeout(() => (copied = false), 1500);
	}
</script>

<div class="code-wrap">
	{@html html}
	<button class="copy-btn" class:copied onclick={copy} title={copied ? 'Copied!' : 'Copy'}>
		{#if copied}
			<svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
				<path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/>
			</svg>
		{:else}
			<svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
				<path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1z"/>
				<path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5H3.5A1.5 1.5 0 0 0 2 3h12a1.5 1.5 0 0 0-1.5-1.5H11A1.5 1.5 0 0 0 9.5 0h-3z"/>
			</svg>
		{/if}
	</button>
</div>

<style>
	.code-wrap {
		position: relative;
	}

	.code-wrap :global(pre) {
		background: #111118 !important;
		border: 1px solid #1e1e2a;
		border-radius: 8px;
		padding: 1rem 1.25rem;
		overflow-x: auto;
		-webkit-overflow-scrolling: touch;
		margin: 0;
	}

	.code-wrap :global(pre code) {
		font-family: ui-monospace, 'Cascadia Code', monospace;
		font-size: 0.82rem;
		line-height: 1.65;
		background: none !important;
	}

	.copy-btn {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		border-radius: 5px;
		border: 1px solid #2a2a3a;
		background: #1a1a28;
		color: #55556a;
		cursor: pointer;
		opacity: 0;
		transition: opacity 0.15s, color 0.15s, background 0.15s;
	}

	.code-wrap:hover .copy-btn {
		opacity: 1;
	}

	.copy-btn:hover {
		background: #222236;
		color: #a5a3ff;
		border-color: #3a3a55;
	}

	.copy-btn.copied {
		opacity: 1;
		color: #5a9a5a;
		border-color: #2a4a2a;
		background: #1a281a;
	}
</style>
