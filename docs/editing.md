# Editing daniellitt.com

## Preview and publish without command-line work

Use [GitHub Desktop](https://desktop.github.com/) to keep the repository synchronized and to publish changes. The same workflow works on each Mac after the repository has been cloned there.

1. In GitHub Desktop, click **Fetch origin** before editing.
2. Edit the Markdown files in any editor.
3. In Finder, double-click **Preview Website.command** at the top of the repository. The first launch downloads a private copy of the required preview tools into the repository's ignored `.site-tools` folder. Later launches reuse them.
4. Wait for the production build and available validation checks to finish. The preview opens automatically in the default browser. Close the launcher window to stop the preview. GitHub repeats the complete validation before publishing.
5. Return to GitHub Desktop, review the changed files, enter a short summary, and click **Commit to main**, then **Push origin**. Updating `main` automatically publishes the site through GitHub Pages.

For changes that should be reviewed before publishing, use GitHub Desktop's **New Branch** button before editing. After previewing, commit and click **Publish branch**, then **Create Pull Request**. GitHub automatically runs the **Build and validate preview** check. When it is green, click **Merge pull request** and **Confirm merge** on GitHub; that merge publishes the site.

The preview runtime and `node_modules` are local to each computer and are not committed. The Markdown content and launcher stay in GitHub, so edits and the workflow travel with the repository.

## Command-line preview (optional for developers)

From this repository, run:

```sh
pnpm site:preview
```

This checks the Astro source, builds the entire production site, validates the preserved URLs, assets, comments, metadata, downloads, and MathJax configuration, and then serves that production build at `http://localhost:4321/`. Stop it with `Control-C`.

While writing an entry marked `draft: true`, run `pnpm dev` instead. Development mode includes drafts, displays a clear draft notice, and does not load FastComments on them. The production build, sitemap, RSS feed, search index, and deployment all exclude drafts.

## Edit existing writing

- Blog posts are in `src/data/blog/`.
- Ordinary pages are in `src/data/pages/`.
- Archived course pages are in `src/data/courses/`.
- The home page and navigation are in `src/pages/index.astro` and `src/components/SiteHeader.astro`.
- Images and downloads are in `public/`; a file at `public/images/example.jpg` is linked as `/images/example.jpg`.

Imported Squarespace entries use clean HTML inside Markdown files. Edit the visible text between tags and keep the surrounding tags balanced. New material can use ordinary Markdown.

## Add or edit a publication

Publication records live in `src/data/publications.yaml`. They are grouped under the same research-section headings
shown on the page. Each record has three principal fields:

```yaml
            - title: |-
                <em>Paper title</em>
              citation: |-
                (<a href="https://arxiv.org/abs/example">arXiv version</a>, 2026, joint with Someone Else)
              abstract: |-
                The abstract goes here, with TeX such as \(E_6\).
```

Copy `templates/new-publication.yaml` beneath the appropriate `publications:` line, retain its indentation, and edit
the three fields. Reorder complete records to change their order on the page. The renderer automatically supplies the
bullet, bold title, collapsed `Abstract` control, and surrounding layout. Inline HTML is allowed for links and emphasis;
TeX in this YAML file uses ordinary single-backslash delimiters such as `\(x\)` and `\[x\]`.

Most abstracts use the original indented quotation styling. Add `quoted: false` to a record only when the abstract
should use the unindented style.

Do not change an imported entry's `legacyPath`. It controls the public URL, canonical URL, and FastComments thread identifier. Changing it would break old links and detach comments.

Set `math: true` on an entry that uses TeX. In new Markdown, write doubled delimiter backslashes such as `\\(x+y\\)` or `\\[x+y\\]`; Markdown emits those as the single-backslash delimiters MathJax needs. Imported HTML already contains single-backslash delimiters and does not need this adjustment. Set `comments: false` only when a published post should not show a comment thread.

## Start a post

Copy the template, then edit the copy:

```sh
cp templates/new-post.md src/data/blog/my-post-slug.md
```

Choose the final date and slug before publishing. Keep `draft: true` while writing and preview it with `pnpm dev`; then set `draft: false` and run `pnpm site:preview` for the complete production check. A new image should normally go in `public/images/blog/my-post-slug/`.

Tags and categories use the following shape when needed:

```yaml
tags: [{"name": "number theory", "path": "/blog/tag/number-theory"}]
categories: [{"name": "math", "path": "/blog/category/math"}]
```

Use empty arrays if none apply. Existing taxonomy paths should be reused exactly.

## Before committing

Double-click **Preview Website.command** and check the changed page at both a wide and a narrow browser width. Confirm that links and downloads work, TeX renders when present, and the comments section appears at the intended immutable URL.
