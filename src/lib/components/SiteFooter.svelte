<script>
	import { base } from '$app/paths';
	import { Youtube, Facebook, Instagram, ExternalLink } from '@lucide/svelte';

	// A project-specific footer (the scrolly-kit Footer only ships youtube/github/
	// linkedin/bluesky icons and a non-clickable logo). Same look, Osher socials.
	let {
		theme = undefined,
		logoSrc = `${base}/UVM_Logo_Primary_Horiz_W_PunchOut.png`,
		logoAlt = 'UVM Osher Center for Integrative Health',
		logoHref = 'https://www.uvm.edu/osher',
		socialLinks = [
			{
				href: 'https://www.youtube.com/channel/UCkm2uT7H78t7uaMyuKhjycg',
				label: 'YouTube',
				icon: 'youtube'
			},
			{ href: 'https://www.facebook.com/UVMOsher', label: 'Facebook', icon: 'facebook' },
			{ href: 'https://www.instagram.com/osheruvm/', label: 'Instagram', icon: 'instagram' },
			{ href: 'https://x.com/uvminthealth', label: 'X (Twitter)', icon: 'x' }
		],
		bottomLinks = [
			{
				href: 'https://www.uvm.edu/equal-opportunity/americans-disabilities-act-and-reasonable-accommodations',
				label: 'Accessibility'
			},
			{
				href: 'https://www.uvm.edu/compliance/website-privacy-policy/terms-use',
				label: 'Privacy/Terms of Use'
			}
		],
		copyright = `© ${new Date().getFullYear()}, Osher Center for Integrative Health`
	} = $props();
</script>

<footer class={['footer', theme === 'light' && 'theme-light', theme === 'dark' && 'theme-dark']}>
	<div class="footer-inner">
		<div class="footer-logo">
			<a href={logoHref} target="_blank" rel="noreferrer" class="logo-link" aria-label={logoAlt}>
				<img src={logoSrc} alt={logoAlt} class="logo-img" />
			</a>
			<ul class="social-icons">
				{#each socialLinks as link (link.href)}
					<li>
						<a href={link.href} target="_blank" rel="noreferrer" aria-label={link.label}>
							{#if link.icon === 'youtube'}
								<Youtube class="icon" size={20} />
							{:else if link.icon === 'facebook'}
								<Facebook class="icon" size={20} />
							{:else if link.icon === 'instagram'}
								<Instagram class="icon" size={20} />
							{:else if link.icon === 'x'}
								<svg
									class="icon"
									width="18"
									height="18"
									viewBox="0 0 24 24"
									fill="currentColor"
									aria-hidden="true"
								>
									<path
										d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
									/>
								</svg>
							{/if}
						</a>
					</li>
				{/each}
			</ul>
		</div>

		<div class="footer-bottom">
			{#each bottomLinks as link (link.href)}
				<a class="cc-footer-copy" href={link.href} target="_blank" rel="noreferrer">
					<span class="link-text">{link.label} <ExternalLink class="icon" size={14} /></span>
				</a>
			{/each}
			<div class="cc-footer-copy">{copyright}</div>
		</div>
	</div>
</footer>

<style>
	.footer {
		width: 100%;
		background-color: var(--footer-bg, var(--vcsi-color-uvm-green));
		border-top: 1px solid var(--footer-border, rgba(255, 255, 255, 0.2));
		padding: var(--vcsi-space-2xl) 0 var(--vcsi-space-xl);
	}

	:global(.dark) .footer:not(.theme-light):not(.theme-dark) {
		background-color: var(--footer-bg, rgb(45, 45, 45));
		border-top-color: var(--footer-border, rgba(255, 255, 255, 0.1));
	}

	.footer.theme-light {
		background-color: var(--vcsi-color-uvm-green);
		border-top-color: rgba(255, 255, 255, 0.2);
	}

	.footer.theme-dark {
		background-color: rgb(45, 45, 45);
		border-top-color: rgba(255, 255, 255, 0.1);
	}

	.footer-inner {
		width: 100%;
		max-width: var(--vcsi-page-max-width);
		margin-inline: auto;
		padding-inline: var(--vcsi-page-inline-padding);
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: var(--vcsi-space-xl);
		align-items: start;
	}

	.footer-logo {
		grid-column: 1;
		display: flex;
		flex-direction: column;
		gap: var(--vcsi-space-sm);
	}

	.logo-link {
		display: inline-block;
		width: fit-content;
		transition: opacity 0.2s ease;
	}

	.logo-link:hover {
		opacity: 0.85;
	}

	.logo-img {
		width: 200px;
		height: auto;
		display: block;
	}

	.footer-bottom {
		grid-column: 1 / -1;
		display: flex;
		flex-wrap: nowrap;
		gap: var(--vcsi-space-lg);
		align-items: center;
		padding-top: var(--vcsi-space-lg);
		margin-top: var(--vcsi-space-md);
		border-top: 1px solid rgba(255, 255, 255, 0.2);
	}

	.social-icons {
		display: flex;
		gap: var(--vcsi-space-md);
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.social-icons a {
		text-decoration: none;
		color: var(--vcsi-color-uvm-gold);
		display: inline-flex;
	}

	.cc-footer-copy {
		color: var(--vcsi-color-white);
		font-weight: 500;
		font-size: 1rem;
		text-decoration: none;
		white-space: nowrap;
	}

	.cc-footer-copy .link-text {
		display: inline-flex;
		align-items: center;
		gap: var(--vcsi-space-xs);
	}

	.cc-footer-copy:last-child {
		margin-left: auto;
	}

	@media (max-width: 768px) {
		.footer-inner {
			grid-template-columns: repeat(2, 1fr);
			grid-template-rows: auto auto auto;
			gap: var(--vcsi-space-lg) var(--vcsi-space-md);
		}

		.footer-logo {
			grid-column: 1 / 3;
			grid-row: 1;
			gap: 0.75rem;
		}

		.footer-bottom {
			grid-column: 1 / 3;
			grid-row: 2;
			flex-wrap: wrap;
			gap: var(--vcsi-space-md);
		}

		.cc-footer-copy {
			font-size: 0.85rem;
		}

		.cc-footer-copy:last-child {
			width: 100%;
			margin-left: 0;
		}
	}
</style>
