# Editing daniellitt.com

## Preview one command

From this repository, run:

```sh
pnpm site:preview
```

This checks the Astro source, builds the entire site, validates the preserved URLs, assets, comments, and MathJax configuration, and starts a preview at `http://localhost:4321/`. Stop it with `Control-C`.

## Edit existing writing

- Blog posts are in `src/data/blog/`.
- Ordinary pages are in `src/data/pages/`.
- Archived course pages are in `src/data/courses/`.
- The home page and navigation are in `src/pages/index.astro` and `src/components/SiteHeader.astro`.
- Images and downloads are in `public/`; a file at `public/images/example.jpg` is linked as `/images/example.jpg`.

Imported Squarespace entries use clean HTML inside Markdown files. Edit the visible text between tags and keep the surrounding tags balanced. New material can use ordinary Markdown.

Do not change an imported entry's `legacyPath`. It controls the public URL, canonical URL, and FastComments thread identifier. Changing it would break old links and detach comments.

Set `math: true` on an entry that uses TeX delimiters such as `\(...\)` or `\[...\]`; otherwise leave it `false`. Set `comments: false` only when a post should not show a comment thread.

## Start a post

Copy the template, then edit the copy:

```sh
cp templates/new-post.md src/data/blog/my-post-slug.md
```

Choose the final date and slug before publishing. Keep `draft: true` while writing, preview the site, then set `draft: false` when the post is ready. A new image should normally go in `public/images/blog/my-post-slug/`.

Tags and categories use the following shape when needed:

```yaml
tags: [{"name": "number theory", "path": "/blog/tag/number-theory"}]
categories: [{"name": "math", "path": "/blog/category/math"}]
```

Use empty arrays if none apply. Existing taxonomy paths should be reused exactly.

## Before committing

Run `pnpm site:preview` and check the changed page at both a wide and a narrow browser width. Confirm that links and downloads work, TeX renders when present, and the comments section appears at the intended immutable URL.
