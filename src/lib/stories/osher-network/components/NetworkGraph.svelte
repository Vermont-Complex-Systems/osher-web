<script>
	import { browser } from '$app/environment';
	import {
		forceSimulation,
		forceLink,
		forceManyBody,
		forceCollide,
		forceX,
		forceY,
		scaleOrdinal
	} from 'd3';

	import allNodes from '../data/nodes.json';
	import edges from '../data/edges.json';

	// ---- geometry (in viewBox units) ----
	// Two elliptical rings: outer = organizations + colleges/centers, inner =
	// departments/divisions. AY squashes the vertical axis into a wide oval so the
	// whole thing fits a screen without scrolling. Radii below are the horizontal
	// (x) radii; the vertical radius of each is R * AY.
	const VBW = 1000;
	const VBH = 680;
	const CX = VBW / 2;
	const CY = VBH / 2;
	const AY = 0.58; // vertical squash factor
	const R_PROJECT = 240; // projects float inside the inner ring
	const R_DEPT = 320; // inner: departments / divisions
	const R_OUTER = 440; // outer: organizations + colleges / centers

	const EGO_ID = 'UVM / Osher Center';

	// `level` (org / unit / dept) and the synthesized org hubs come from the
	// wrangler (network.py) — the component only lays them out.
	const entities = allNodes.filter((n) => n.type === 'org');
	const orgsList = [...new Set(entities.map((n) => n.organization))];
	const orgTypeOf = new Map(entities.map((n) => [n.organization, n.organization_type]));

	const egoEntity = entities.find((n) => n.id === EGO_ID);
	const orgRing = entities.filter((n) => n.level === 'org');
	const unitRing = entities.filter((n) => n.level === 'unit' && n.id !== EGO_ID);
	const deptRing = entities.filter((n) => n.level === 'dept');

	// ---- color = the TYPE at each node's own level ----
	// Departments have no type of their own, so the whole inner ring is just
	// "Department" (or "Division"); this keeps unit types (College, Center;
	// Institute, …) on the outer ring where they belong. Units / organizations
	// use their unit type, falling back to their organization type.
	const colorKey = (n) =>
		n.level === 'dept'
			? n.division && !n.department
				? 'Division'
				: 'Department'
			: n.college_unit_type || n.organization_type;

	const PALETTE = [
		'#154734', '#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#EDC948',
		'#B07AA1', '#FF9DA7', '#9C755F', '#BAB0AC', '#86BCB6', '#D37295',
		'#8CD17D', '#B6992D', '#499894', '#79706E', '#FABFD2', '#A0CBE8'
	];
	const colorDomain = [...new Set(entities.map(colorKey))].sort();
	const color = scaleOrdinal().domain(colorDomain).range(PALETTE);

	// colors present on each ring, for the two-row legend (kept in colorDomain order)
	const outerSet = new Set([...orgRing, ...unitRing].map(colorKey));
	const innerSet = new Set(deptRing.map(colorKey));
	const outerColorKeys = colorDomain.filter((k) => outerSet.has(k));
	const innerColorKeys = colorDomain.filter((k) => innerSet.has(k));

	// ---- angular sectors: one wedge per organization, sized by its node count,
	// so a given org occupies the same angle across all three rings (radial wedges)
	const weightOf = new Map(orgsList.map((o) => [o, 0]));
	for (const n of [...orgRing, ...unitRing, ...deptRing]) {
		weightOf.set(n.organization, (weightOf.get(n.organization) ?? 0) + 1);
	}
	// order wedges around the circle by organization type, then name
	const wedgeOrder = [...orgsList].sort((a, b) =>
		`${orgTypeOf.get(a)} ${a}`.localeCompare(`${orgTypeOf.get(b)} ${b}`)
	);
	const totalW = [...weightOf.values()].reduce((a, b) => a + b, 0) || 1;
	const sector = new Map();
	let acc = 0;
	for (const o of wedgeOrder) {
		const start = -Math.PI / 2 + (2 * Math.PI * acc) / totalW;
		acc += weightOf.get(o) || 0;
		const end = -Math.PI / 2 + (2 * Math.PI * acc) / totalW;
		sector.set(o, { start, end });
	}

	// deterministic hash-based jitter in [-amp, amp] — same every render (SSR-safe)
	function hashStr(s) {
		let h = 0;
		for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
		return h;
	}
	function jitter(seed, amp) {
		const s = Math.sin(seed * 127.1) * 43758.5453;
		return (s - Math.floor(s) - 0.5) * 2 * amp;
	}

	// place a ring level: within each org's wedge, spread that org's nodes evenly.
	// Nodes are soft-anchored (ax/ay) so they jiggle a touch as the sim settles.
	function placeRing(list, radius) {
		const byOrg = new Map();
		for (const n of list) {
			if (!byOrg.has(n.organization)) byOrg.set(n.organization, []);
			byOrg.get(n.organization).push(n);
		}
		const out = [];
		for (const [o, group] of byOrg) {
			group.sort((a, b) => `${a.college_unit}${a.label}`.localeCompare(`${b.college_unit}${b.label}`));
			const { start, end } = sector.get(o);
			const span = end - start;
			const pad = Math.min(span * 0.18, 0.1);
			const s = start + pad;
			const e = end - pad;
			group.forEach((n, i) => {
				const t = group.length === 1 ? 0.5 : i / (group.length - 1);
				const seed = hashStr(n.id);
				const angle = s + (e - s) * t + jitter(seed, 0.015);
				const rad = radius + jitter(seed + 7, 5);
				const ax = CX + rad * Math.cos(angle);
				const ay = CY + rad * AY * Math.sin(angle);
				out.push({
					...n,
					kind: 'org',
					angle,
					ax,
					ay,
					x: ax,
					y: ay,
					r: n.level === 'org' ? 7 : 6
				});
			});
		}
		return out;
	}

	const ego = { ...egoEntity, kind: 'ego', level: 'ego', fx: CX, fy: CY, x: CX, y: CY, angle: 0, r: 16 };

	const orgNodes = [
		ego,
		...placeRing([...orgRing, ...unitRing], R_OUTER), // organizations + colleges/centers together
		...placeRing(deptRing, R_DEPT) // departments / divisions
	];

	// projects: free-floating, seeded on a deterministic golden-angle spiral near the center
	const projectNodes = allNodes
		.filter((n) => n.type === 'project')
		.map((n, i) => {
			const a = i * 2.399963; // golden angle
			const rr = 25 + 7 * Math.sqrt(i);
			return { ...n, kind: 'project', x: CX + rr * Math.cos(a), y: CY + rr * AY * Math.sin(a), r: 6 };
		});

	const nodeObjs = [...orgNodes, ...projectNodes];
	const linkObjs = edges.map((e) => ({ source: e.source, target: e.target }));

	// adjacency, for click-to-highlight
	const neighbors = new Map();
	for (const e of edges) {
		if (!neighbors.has(e.source)) neighbors.set(e.source, new Set());
		if (!neighbors.has(e.target)) neighbors.set(e.target, new Set());
		neighbors.get(e.source).add(e.target);
		neighbors.get(e.target).add(e.source);
	}
	const isNeighbor = (id, ofId) => neighbors.get(ofId)?.has(id) ?? false;

	// ---- reactive snapshots the template renders from ----
	let renderNodes = $state(nodeObjs.map((n) => ({ ...n })));
	let renderLinks = $state([]);

	$effect(() => {
		if (!browser) return;

		const sim = forceSimulation(nodeObjs)
			.force(
				'link',
				forceLink(linkObjs)
					.id((d) => d.id)
					.distance(120)
					.strength(0.06)
			)
			.force('charge', forceManyBody().strength((d) => (d.kind === 'project' ? -50 : 0)))
			.force('collide', forceCollide((d) => d.r + 3))
			// org rings are soft-anchored to their ideal slot (so they jiggle a little
			// instead of snapping to a perfect circle); projects drift gently to center
			.force(
				'x',
				forceX((d) => (d.kind === 'org' ? d.ax : CX)).strength((d) =>
					d.kind === 'org' ? 0.5 : d.kind === 'project' ? 0.02 : 0
				)
			)
			.force(
				'y',
				forceY((d) => (d.kind === 'org' ? d.ay : CY)).strength((d) =>
					d.kind === 'org' ? 0.5 : d.kind === 'project' ? 0.02 : 0
				)
			)
			.on('tick', () => {
				// keep projects inside the inner ellipse, and off the ego at the center
				const rx = R_PROJECT;
				const ry = R_PROJECT * AY;
				for (const n of nodeObjs) {
					if (n.kind !== 'project') continue;
					const dx = (n.x - CX) / rx;
					const dy = (n.y - CY) / ry;
					const d = Math.hypot(dx, dy) || 1;
					const clamp = d > 1 ? 1 : d < 0.18 ? 0.18 : null;
					if (clamp !== null) {
						n.x = CX + (dx / d) * clamp * rx;
						n.y = CY + (dy / d) * clamp * ry;
					}
				}
				renderNodes = nodeObjs.map((n) => ({ ...n }));
				renderLinks = linkObjs.map((l) => ({
					x1: l.source.x,
					y1: l.source.y,
					x2: l.target.x,
					y2: l.target.y,
					sourceId: l.source.id,
					targetId: l.target.id
				}));
			});

		return () => sim.stop();
	});

	function fill(n) {
		if (n.kind === 'ego') return '#FFB81C'; // UVM gold — the ego stands apart
		if (n.kind === 'project') return '#e8e2da';
		return color(colorKey(n));
	}

	// human-readable level label for the tooltip
	function levelLabel(n) {
		if (n.kind === 'ego') return 'Osher Center · the hub';
		if (n.level === 'org') return 'Organization';
		if (n.level === 'unit') return n.college_unit_type || 'College / unit';
		if (n.level === 'dept') return n.division ? 'Division' : 'Department';
		return '';
	}

	// ---- hover / focus tooltip (a small card that follows the pointer) ----
	let hoveredNode = $state(null);
	let tipX = $state(0);
	let tipY = $state(0);
	let tipFlip = $state(false); // flip to the left of the pointer near the right edge

	function hoverPath(n) {
		return [n.organization, n.college_unit, n.department || n.division]
			.filter(Boolean)
			.join(' › ');
	}

	function move(event, n) {
		hoveredNode = n;
		tipX = event.clientX;
		tipY = event.clientY;
		tipFlip = event.clientX > window.innerWidth - 240;
	}
	function focusNode(event, n) {
		const r = event.currentTarget.getBoundingClientRect();
		hoveredNode = n;
		tipX = r.x + r.width / 2;
		tipY = r.y;
		tipFlip = tipX > window.innerWidth - 240;
	}
	function leave() {
		hoveredNode = null;
	}

	// ---- click to highlight a node, its edges and neighbors ----
	let selectedId = $state(null);

	function select(event, n) {
		event.stopPropagation();
		selectedId = selectedId === n.id ? null : n.id;
	}
	function onKey(event, n) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			selectedId = selectedId === n.id ? null : n.id;
		} else if (event.key === 'Escape') {
			selectedId = null;
		}
	}
	function clearSelect() {
		selectedId = null;
	}

	// a node is dimmed when something else is selected and it's neither the
	// selection nor one of its neighbors
	const isDim = (n) => selectedId && n.id !== selectedId && !isNeighbor(n.id, selectedId);
	// a link is lit when nothing is selected, or it touches the selection
	const isLit = (l) => !selectedId || l.sourceId === selectedId || l.targetId === selectedId;
</script>

<figure class="network">
	<svg viewBox="0 0 {VBW} {VBH}" role="img" aria-label="Osher Center ego network of organizations and projects">
		<!-- click empty space to clear the selection -->
		<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
		<rect x="0" y="0" width={VBW} height={VBH} fill="transparent" onclick={clearSelect} />

		<!-- title, in the empty top-left corner -->
		<g class="map-title">
			<text x="6" y="17">The Osher Center collaboration map</text>
			<text class="map-subtitle" x="6" y="40">click on nodes to highlight collaborations</text>
		</g>

		<!-- ring guides -->
		<ellipse class="guide" cx={CX} cy={CY} rx={R_DEPT} ry={R_DEPT * AY} />
		<ellipse class="guide" cx={CX} cy={CY} rx={R_OUTER} ry={R_OUTER * AY} />

		<!-- edges -->
		<g class="edges">
			{#each renderLinks as l, i (i)}
				<line
					x1={l.x1}
					y1={l.y1}
					x2={l.x2}
					y2={l.y2}
					stroke-opacity={selectedId ? (isLit(l) ? 0.55 : 0.03) : 0.1}
				/>
			{/each}
		</g>

		<!-- nodes -->
		<g class="nodes">
			{#each renderNodes as n (n.id)}
				{@const sel = selectedId === n.id}
				{@const active = sel || hoveredNode?.id === n.id}
				{@const dim = isDim(n)}
				{#if n.kind === 'project'}
					<rect
						class="node"
						class:dim
						x={n.x - n.r}
						y={n.y - n.r}
						width={n.r * 2}
						height={n.r * 2}
						fill={fill(n)}
						stroke={active ? '#111' : '#6b6b6b'}
						stroke-width={active ? 2.5 : 1}
						role="button"
						tabindex="0"
						aria-label={n.label}
						aria-pressed={sel}
						onclick={(e) => select(e, n)}
						onkeydown={(e) => onKey(e, n)}
						onmousemove={(e) => move(e, n)}
						onmouseleave={leave}
						onfocus={(e) => focusNode(e, n)}
						onblur={leave}
					/>
				{:else}
					<circle
						class="node"
						class:dim
						cx={n.x}
						cy={n.y}
						r={active ? n.r + 2 : n.r}
						fill={fill(n)}
						stroke={active ? '#111' : '#fff'}
						stroke-width={active ? 2.5 : 1.5}
						role="button"
						tabindex="0"
						aria-label={n.label}
						aria-pressed={sel}
						onclick={(e) => select(e, n)}
						onkeydown={(e) => onKey(e, n)}
						onmousemove={(e) => move(e, n)}
						onmouseleave={leave}
						onfocus={(e) => focusNode(e, n)}
						onblur={leave}
					/>
				{/if}
			{/each}
		</g>

		<!-- labels: rings fan out radially, projects sit above their node -->
		<g class="labels">
			{#each renderNodes as n (n.id)}
				{#if n.kind === 'ego'}
					<text x={n.x} y={n.y + n.r + 18} text-anchor="middle" class="ego-label" class:dim={isDim(n)}>
						{n.short}
					</text>
				{:else if n.kind === 'project'}
					<text
						class="proj-label"
						class:dim={isDim(n)}
						x={n.x}
						y={n.y - n.r - 3}
						text-anchor="middle"
					>
						{n.short}
					</text>
				{:else}
					{@const flip = Math.cos(n.angle) < 0}
					<text
						class="node-label"
						class:dim={isDim(n)}
						transform="translate({n.x},{n.y}) rotate({(n.angle * 180) / Math.PI + (flip ? 180 : 0)})"
						x={flip ? -(n.r + 4) : n.r + 4}
						text-anchor={flip ? 'end' : 'start'}
						dominant-baseline="middle"
					>
						{n.short}
					</text>
				{/if}
			{/each}
		</g>
	</svg>

	{#if hoveredNode}
		<div
			class="tip-card"
			role="tooltip"
			style="left:{tipX}px; top:{tipY}px; transform: translate({tipFlip
				? 'calc(-100% - 14px)'
				: '14px'}, calc(-100% - 12px));"
		>
			<div class="tip-head">
				<span
					class="tip-dot"
					class:square={hoveredNode.kind === 'project'}
					style="background:{fill(hoveredNode)}"
				></span>
				<strong>{hoveredNode.label}</strong>
			</div>
			{#if hoveredNode.kind === 'project'}
				<div class="tip-kind">Project</div>
				<div class="tip-stat">{hoveredNode.n_orgs} organizations involved</div>
			{:else}
				<div class="tip-kind">{levelLabel(hoveredNode)}</div>
				{#if hoverPath(hoveredNode)}
					<div class="tip-path">{hoverPath(hoveredNode)}</div>
				{/if}
				<div class="tip-stat">
					{hoveredNode.organization_type}{#if !hoveredNode.synthetic} · {hoveredNode.n_projects} projects{/if}
				</div>
			{/if}
		</div>
	{/if}

	<figcaption class="legend">
		<div class="legend-row">
			<span class="legend-level">Outer ring</span>
			{#each outerColorKeys as key (key)}
				<span class="legend-item"><span class="swatch" style="background:{color(key)}"></span>{key}</span>
			{/each}
		</div>
		<div class="legend-row">
			<span class="legend-level">Inner ring</span>
			{#each innerColorKeys as key (key)}
				<span class="legend-item"><span class="swatch" style="background:{color(key)}"></span>{key}</span>
			{/each}
			<span class="legend-item"><span class="swatch square"></span>Project</span>
		</div>
	</figcaption>
</figure>

<style>
	.network {
		margin: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--vcsi-space-md, 1rem);
	}

	svg {
		width: 100%;
		max-width: min(1200px, 96vw);
		max-height: 82vh; /* keep the oval on-screen without scrolling */
		height: auto;
		display: block;
	}

	/* labels never intercept the pointer — hover/click always hits the node */
	.labels {
		pointer-events: none;
	}

	.map-title {
		pointer-events: none;
	}

	.map-title text {
		fill: currentColor;
		font-family: var(--vcsi-font-sans, system-ui);
		font-size: 22px;
		font-weight: 700;
	}

	.map-title .map-subtitle {
		font-size: 13px;
		font-weight: 400;
		font-style: italic;
		fill: color-mix(in srgb, currentColor 50%, transparent);
	}

	.node {
		cursor: pointer;
		transition:
			stroke-width 0.12s ease,
			opacity 0.2s ease,
			r 0.12s ease;
	}

	.node:focus {
		outline: none;
	}

	/* faded when another node is selected */
	.dim {
		opacity: 0.15;
		transition: opacity 0.2s ease;
	}

	.edges line {
		transition: stroke-opacity 0.2s ease;
	}

	/* tooltip card — fixed to the viewport, follows the pointer */
	.tip-card {
		position: fixed;
		z-index: 10;
		pointer-events: none;
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		min-width: 9rem;
		max-width: 16rem;
		line-height: 1.3;
		padding: 0.5rem 0.65rem;
		background: var(--vcsi-bg, #fff);
		color: var(--vcsi-fg, #222);
		border: 1px solid var(--vcsi-border, rgba(0, 0, 0, 0.12));
		border-radius: var(--vcsi-radius-md, 6px);
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
		font-size: 0.8rem;
	}

	.tip-head {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.95rem;
	}

	.tip-dot {
		width: 0.7rem;
		height: 0.7rem;
		border-radius: 50%;
		flex: none;
		border: 1px solid rgba(0, 0, 0, 0.25);
	}

	.tip-dot.square {
		border-radius: 2px;
	}

	.tip-kind {
		font-size: 0.8rem;
		font-weight: 600;
		opacity: 0.75;
	}

	.tip-path {
		font-size: 0.75rem;
		opacity: 0.7;
	}

	.tip-stat {
		font-size: 0.78rem;
		margin-top: 0.15rem;
		opacity: 0.9;
	}

	.guide {
		fill: none;
		stroke: currentColor;
		stroke-opacity: 0.12;
		stroke-dasharray: 3 5;
	}

	.edges line {
		stroke: currentColor;
		/* opacity is set per-line via the stroke-opacity attribute so selection can drive it */
	}

	.labels text {
		fill: currentColor;
		font-family: var(--vcsi-font-sans, system-ui);
	}

	.node-label {
		font-size: 10px;
	}

	.proj-label {
		font-size: 8px;
		fill: color-mix(in srgb, currentColor 65%, transparent);
	}

	.ego-label {
		font-weight: 700;
		font-size: 16px;
	}

	.legend {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		font-size: 0.78rem;
		max-width: min(1200px, 96vw);
		width: 100%;
	}

	/* one row per ring (outer / inner); items wrap only if they truly overflow */
	.legend-row {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 0.3rem 0.85rem;
	}

	.legend-level {
		flex: 0 0 5rem;
		text-align: right;
		font-weight: 600;
		opacity: 0.6;
		font-size: 0.72rem;
	}

	/* the legend eats too much vertical space on phones — desktop only */
	@media (max-width: 768px) {
		.legend {
			display: none;
		}
	}

	.legend-item {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		white-space: nowrap;
	}

	.swatch {
		width: 0.75rem;
		height: 0.75rem;
		border-radius: 50%;
		display: inline-block;
	}

	.swatch.square {
		border-radius: 2px;
		background: #e8e2da;
		border: 1px solid #6b6b6b;
	}
</style>
