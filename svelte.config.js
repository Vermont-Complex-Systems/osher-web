import adapter from '@sveltejs/adapter-static'
import { readFileSync } from 'fs';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte'

// Example of how to dynamically prerender members in static web app.
// There might be a better way to do that at some point.
const membersCSV = readFileSync('src/lib/data/members.csv', 'utf-8');
const memberIds = membersCSV.split('\n').slice(1).filter(line => line.trim()).map(line => line.split(',')[0]);

const storiesCSV = readFileSync('src/lib/data/stories.csv', 'utf-8');
const storiesIds = storiesCSV.split('\n').slice(1).filter(line => line.trim()).map(line => line.split(',')[0]);

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		prerender: {
			entries: [
				'*',
				...memberIds.map(id => `/about/${id}`),
				...storiesIds.map(id => `/${id}`)
			]
		},
		adapter: adapter(),
		// On GitHub Pages project sites the app is served under /<repo>. The deploy
		// workflow sets BASE_PATH; locally it's empty so dev/build work unchanged.
		paths: {
			base: process.env.BASE_PATH || '',
		},
		experimental: {
			remoteFunctions: true,
		},
	},
	compilerOptions: {
		experimental: {
			async: true,
		},
	},
	vitePlugin: {
		inspector: true,
	},
}

export default config