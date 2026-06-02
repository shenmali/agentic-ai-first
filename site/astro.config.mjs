import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';

// NOTE: @astrojs/sitemap is deferred to Plan 3 (SEO task) — sitemap 3.7.3 is
// incompatible with astro 4.16's build:done hook (_routes undefined). Re-enable
// with a compatible version in Plan 3 Task 5.

export default defineConfig({
  site: 'https://agentic.mashen.dev',
  integrations: [mdx()],
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'tr', 'nl'],
    routing: { prefixDefaultLocale: true },
  },
});
