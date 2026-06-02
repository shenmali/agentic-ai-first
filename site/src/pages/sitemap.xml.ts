import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { LOCALES } from '../i18n/utils';

// Manual sitemap: @astrojs/sitemap 3.7.x is incompatible with astro 4.16's
// build:done hook, so we emit our own (one entry per locale × landing + slug).
const SITE = 'https://agentic.mashen.dev';

export const GET: APIRoute = async () => {
  const all = await getCollection('posts');
  const slugs = [...new Set(all.map((p) => p.data.urlSlug))];
  const urls: string[] = [];
  for (const lang of LOCALES) {
    urls.push(`${SITE}/${lang}/`);
    for (const slug of slugs) urls.push(`${SITE}/${lang}/${slug}`);
  }
  const body =
    '<?xml version="1.0" encoding="UTF-8"?>\n' +
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    urls.map((u) => `  <url><loc>${u}</loc></url>`).join('\n') +
    '\n</urlset>\n';
  return new Response(body, { headers: { 'Content-Type': 'application/xml' } });
};
