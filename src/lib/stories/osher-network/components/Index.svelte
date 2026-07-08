<script lang="ts">
	import SiteFooter from '$lib/components/SiteFooter.svelte';
	import NetworkGraph from './NetworkGraph.svelte';

	let { story, data } = $props();
</script>

<article class="story">
	<div class="full-bleed">
		<NetworkGraph />
	</div>
</article>

<SiteFooter />
