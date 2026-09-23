import { onMount } from 'svelte';
import { replaceState } from '$app/navigation';
import { page as appPage } from '$app/state';

/**
 * Search query and page number for a paginated list, mirrored into `?q=` and `?page=`
 * so a filtered view can be linked. Prerendered pages cannot read search params at
 * build time, so they are picked up once the page mounts.
 */
export class ListState {
	query = $state('');
	page = $state(1);
	#mounted = false;

	constructor() {
		onMount(() => {
			// Read the address bar rather than page.url, which does not reflect replaceState
			// when returning to this entry with the back button.
			// eslint-disable-next-line svelte/prefer-svelte-reactivity -- read once, never mutated
			const params = new URLSearchParams(location.search);
			this.query = params.get('q') ?? '';
			this.page = Math.max(1, Number.parseInt(params.get('page') ?? '', 10) || 1);
			this.#mounted = true;
		});

		$effect(() => {
			const query = this.query.trim();
			const page = this.page;
			if (!this.#mounted) return;
			const search = [query && `q=${encodeURIComponent(query)}`, page > 1 && `page=${page}`]
				.filter(Boolean)
				.join('&');
			const href = `${location.pathname}${search ? `?${search}` : ''}${location.hash}`;
			if (href === location.pathname + location.search + location.hash) return;
			// eslint-disable-next-line svelte/no-navigation-without-resolve -- same page, only the query changes
			replaceState(href, appPage.state);
		});
	}

	/** Call when the query changes so results start from the first page. */
	resetPage = () => {
		this.page = 1;
	};
}

export function pageSlice<T>(items: T[], page: number, size: number): T[] {
	return items.slice((page - 1) * size, page * size);
}

export function pageCount(total: number, size: number): number {
	return Math.max(1, Math.ceil(total / size));
}
