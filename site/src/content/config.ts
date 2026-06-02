import { defineCollection, z } from 'astro:content';

const posts = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    publishDate: z.coerce.date(),
    lang: z.enum(['en', 'tr', 'nl']),
    urlSlug: z.string(), // routing slug; `slug` is reserved by Astro content collections
    spaceUrl: z.string().url(),
    githubPath: z.string(),
    order: z.number(),
    layer: z.enum(['pattern', 'production', 'flagship']),
  }),
});

export const collections = { posts };
