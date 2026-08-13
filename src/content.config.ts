import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const blog = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/data/blog" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    published: z.coerce.date(),
    updated: z.coerce.date().optional(),
    draft: z.boolean().default(false),
    tags: z.array(z.object({ name: z.string(), path: z.string().startsWith("/blog/tag/") })).default([]),
    categories: z
      .array(z.object({ name: z.string(), path: z.string().startsWith("/blog/category/") }))
      .default([]),
    comments: z.boolean().default(true),
    math: z.boolean().default(false),
    legacyPath: z.string().startsWith("/blog/"),
    imported: z.boolean().default(false),
  }),
});

const pages = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/data/pages" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    legacyPath: z.string().startsWith("/"),
    math: z.boolean().default(false),
    imported: z.boolean().default(false),
  }),
});

const courses = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/data/courses" }),
  schema: z.object({
    title: z.string(),
    code: z.string(),
    institution: z.string(),
    term: z.string().optional(),
    summary: z.string(),
    archived: z.boolean().default(true),
    legacyPath: z.string().startsWith("/").endsWith(".html"),
    sections: z.array(
      z.object({
        id: z.string(),
        label: z.string(),
      }),
    ),
  }),
});

export const collections = { blog, courses, pages };
