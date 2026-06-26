import adapter from '@sveltejs/adapter-static';

const config = {
	compilerOptions: {
		// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
		runes: ({ filename }) =>
			filename.split(/[/\\]/).includes('node_modules') ? undefined : true
	},
	kit: {
		adapter: adapter({ fallback: '404.html' }),
		prerender: {
			handleHttpError: ({ path, message }) => {
				// Instrument index files only exist for assets that appear in instruments.
				if (path.startsWith('/api/instruments/index/')) return;
				throw new Error(message);
			}
		}
	}
};

export default config;
