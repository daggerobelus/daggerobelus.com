import { defineCollection, z } from 'astro:content';

const projects = defineCollection({
  type: 'content',
  schema: ({ image }) => z.object({
    title: z.string(),
    description: z.string(),
    publishDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    image: image().optional(),
    imageAlt: z.string().optional(),
    status: z.enum(['draft', 'in-progress', 'published']).default('published'),
    tags: z.array(z.string()).optional(),
    featured: z.boolean().default(false),
  }),
});

const chapters = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    project: z.string(),
    order: z.number(),
    publishDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    status: z.enum(['draft', 'published']).default('published'),
  }),
});

const tools = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    publishDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    status: z.enum(['draft', 'published']).default('published'),
    download: z.string().optional(),
    promptFile: z.string().optional(),
  }),
});

export const collections = { projects, chapters, tools };
