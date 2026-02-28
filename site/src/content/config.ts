import { defineCollection, z } from 'astro:content';

const projects = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    publishDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    image: z.string().optional(),
    imageAlt: z.string().optional(),
    status: z.enum(['draft', 'in-progress', 'published']).default('published'),
    tags: z.array(z.string()).optional(),
    featured: z.boolean().default(false),
  }),
});

const fieldNotes = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    publishDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    status: z.enum(['draft', 'published']).default('published'),
    tags: z.array(z.string()).optional(),
  }),
});

export const collections = { projects, 'field-notes': fieldNotes };
