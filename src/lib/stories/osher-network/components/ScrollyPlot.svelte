<script>
	import { Tween } from 'svelte/motion';
	import data from '../data/data.csv';

	let { scrollyIndex } = $props();

	let highlighted = $derived(
		scrollyIndex === 0 ? null :
		scrollyIndex === 1 ? 'B' :
		scrollyIndex === 2 ? 'A' : 'all'
	);

	// Tween the Y-axis max value to "zoom in" on the data
	// Tween.of() reactively tracks the derived value
	const maxValue = Tween.of(() => scrollyIndex >= 3 ? 35 : 60, { duration: 600 });

	const width = 300;
	const height = 200;
	const barWidth = 40;
	const gap = 15;
	const marginY = 40;

	// Center bars horizontally
	const totalBarsWidth = data.length * barWidth + (data.length - 1) * gap;
	const marginX = (width - totalBarsWidth) / 2;
</script>

<div class="chart">
	<svg viewBox="0 0 {width} {height}">
		{#each data as d, i}
			{@const value = +d.value}
			{@const barHeight = (value / maxValue.current) * (height - marginY)}
			{@const x = marginX + i * (barWidth + gap)}
			{@const y = height - marginY - barHeight}
			{@const isHighlighted = highlighted === 'all' || highlighted === d.label}

			<rect
				{x}
				{y}
				width={barWidth}
				height={barHeight}
				fill={isHighlighted ? 'var(--vcsi-color-accent, #154734)' : '#ccc'}
				rx="4"
				style="transition: fill 0.3s ease;"
			/>
			<text
				x={x + barWidth / 2}
				y={height - marginY + 15}
				text-anchor="middle"
				font-size="12"
			>
				{d.label}
			</text>
		{/each}
	</svg>
</div>

<style>
	.chart {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	svg {
		max-width: 100%;
		height: auto;
	}

	text {
		fill: currentColor;
	}
</style>
