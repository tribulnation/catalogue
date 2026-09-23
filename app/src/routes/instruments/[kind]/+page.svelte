<script lang="ts">
	import InstrumentList from './InstrumentList.svelte';

	let { data } = $props();
</script>

<!-- Remount per kind so the search state and loaded list start fresh. -->
{#key data.kind}
	<InstrumentList {data} />
{/key}
