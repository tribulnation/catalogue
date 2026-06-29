<script lang="ts">
	export type MultiSelectOption = {
		value: string;
		label: string;
		icon?: string;
		iconFallback?: string;
	};

	let {
		options = [],
		value = $bindable([]),
		placeholder = 'Select…',
		clearLabel = 'Clear',
	}: {
		options: MultiSelectOption[];
		value?: string[];
		placeholder?: string;
		clearLabel?: string;
	} = $props();

	let open = $state(false);
	let comboRef: HTMLDivElement | undefined;

	$effect(() => {
		if (!open) return;
		function handleClick(e: MouseEvent) {
			if (comboRef && !comboRef.contains(e.target as Node)) open = false;
		}
		document.addEventListener('click', handleClick, true);
		return () => document.removeEventListener('click', handleClick, true);
	});

	const selectedLabel = $derived.by(() => {
		if (value.length === 0) return placeholder;
		if (value.length <= 3) return value.join(', ');
		return `${value.length} selected`;
	});

	function toggle(v: string) {
		value = value.includes(v) ? value.filter((x) => x !== v) : [...value, v];
	}

	function clear() {
		value = [];
	}
</script>

<div class="ms" bind:this={comboRef}>
	<button
		type="button"
		class="trigger"
		class:active={value.length > 0}
		aria-expanded={open}
		aria-haspopup="listbox"
		onclick={() => (open = !open)}
	>
		<span class="trigger-text">{selectedLabel}</span>
		<svg class="chevron" xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
			<path d="M6 9l6 6 6-6" />
		</svg>
	</button>

	{#if open}
		<div class="panel" role="listbox">
			{#if value.length > 0}
				<button type="button" class="clear" onclick={clear}>{clearLabel}</button>
			{/if}
			<div class="list">
				{#each options as opt (opt.value)}
					<label class="item">
						<input type="checkbox" checked={value.includes(opt.value)} onchange={() => toggle(opt.value)} />
						{#if opt.icon}
							<img src={opt.icon} alt="" class="opt-icon" width="18" height="18" />
						{:else if opt.iconFallback}
							<span class="opt-icon-fallback">{opt.iconFallback}</span>
						{/if}
						<span class="item-label">{opt.label}</span>
					</label>
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.ms {
		position: relative;
	}

	.trigger {
		display: inline-flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		min-width: 9rem;
		padding: 0.5rem 0.875rem;
		background: #111116;
		border: 1px solid #2a2a38;
		border-radius: 6px;
		color: #8888a0;
		font-size: 0.875rem;
		font-family: inherit;
		cursor: pointer;
		text-align: left;
		transition: border-color 0.12s, color 0.12s;
	}

	.trigger:hover {
		border-color: #3a3a58;
		color: #e4e4eb;
	}

	.trigger[aria-expanded='true'],
	.trigger.active {
		border-color: #4f46e5;
		color: #e4e4eb;
	}

	.trigger-text {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.chevron {
		flex-shrink: 0;
		opacity: 0.6;
		transition: transform 0.15s ease;
	}

	.trigger[aria-expanded='true'] .chevron {
		transform: rotate(180deg);
	}

	.panel {
		position: absolute;
		top: calc(100% + 4px);
		left: 0;
		min-width: 100%;
		max-height: 16rem;
		overflow-y: auto;
		background: #111116;
		border: 1px solid #2a2a38;
		border-radius: 6px;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
		z-index: 50;
		padding: 0.4rem;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.clear {
		font-size: 0.75rem;
		color: #4f46e5;
		background: none;
		border: none;
		cursor: pointer;
		padding: 0.1rem 0.4rem 0.3rem;
		text-decoration: underline;
		font-family: inherit;
		align-self: flex-start;
	}

	.clear:hover {
		color: #a5a3ff;
	}

	.list {
		display: flex;
		flex-direction: column;
		gap: 1px;
	}

	.item {
		display: flex;
		align-items: center;
		gap: 0.45rem;
		cursor: pointer;
		font-size: 0.875rem;
		padding: 0.35rem 0.5rem;
		border-radius: 4px;
		color: #e4e4eb;
		user-select: none;
		transition: background 0.1s;
	}

	.item:hover {
		background: #1a1a24;
	}

	.item input {
		margin: 0;
		accent-color: #4f46e5;
		flex-shrink: 0;
	}

	.item-label {
		font-weight: 500;
	}

	.opt-icon {
		width: 18px;
		height: 18px;
		border-radius: 50%;
		object-fit: contain;
		flex-shrink: 0;
	}

	.opt-icon-fallback {
		width: 18px;
		height: 18px;
		border-radius: 50%;
		background: #2a2a38;
		color: #55556a;
		font-size: 0.6rem;
		font-weight: 600;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		text-transform: uppercase;
	}
</style>
