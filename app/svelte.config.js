import { existsSync, readFileSync } from 'node:fs';
import adapter from '@sveltejs/adapter-static';

// /assets is paginated, so the prerender crawler no longer reaches every asset page
// through links. scripts/build_api.py writes the asset list before the site is built.
const assetList = new URL('./static/api/v1/assets.json', import.meta.url);
const assetPages = existsSync(assetList)
	? JSON.parse(readFileSync(assetList, 'utf8')).map(({ id }) => `/assets/${id}`)
	: [];

const config = {
	compilerOptions: {
		// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
		runes: ({ filename }) =>
			filename.split(/[/\\]/).includes('node_modules') ? undefined : true
	},
	kit: {
		adapter: adapter({ fallback: '404.html' }),
		prerender: {
			entries: ['*', ...assetPages],
			handleHttpError: ({ path, message }) => {
				// Instrument index files only exist for assets that appear in instruments.
				if (path.startsWith('/api/v1/instruments/index/')) return;
				throw new Error(message);
			}
		}
	}
};

export default config;
