<script>
	import { Nav } from '@the-vcsi/scrolly-kit';
	import { base } from '$app/paths';
	import SiteFooter from '$lib/components/SiteFooter.svelte';

	let { children } = $props();
</script>

<Nav
	logoSrc={`${base}/waxSealSmall.png`}
	homeHref={`${base}/`}
	links={[{ href: `${base}/about`, label: 'About' }]}
/>

<main id="content">
	{@render children?.()}
</main>

<SiteFooter />