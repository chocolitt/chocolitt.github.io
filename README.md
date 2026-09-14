# daniellitt.com

Astro source for the production site at `https://www.daniellitt.com`, hosted by GitHub Pages. The Squarespace-to-Astro migration launched on August 17, 2026 and completed its two-week monitoring and retirement checklist on August 31, 2026.

## Preview

Requires Node.js 24.19 and pnpm 11.19.

```sh
pnpm install --frozen-lockfile
cp .env.example .env
```

Set `PUBLIC_FASTCOMMENTS_TENANT_ID` in `.env` to load the real comment widget. The value is a public browser identifier, but the local environment file remains ignored so preview configuration is not committed accidentally.

Build, validate, and open the local preview server with one command:

```sh
pnpm site:preview
```

Then open `http://localhost:4321/`. See [`docs/editing.md`](docs/editing.md) for the concise editing workflow.

When writing a post with `draft: true`, use `pnpm dev` instead; draft entries are deliberately excluded from the production-style preview.

## Content

- Blog posts live in `src/data/blog/`.
- Ordinary Squarespace pages live in `src/data/pages/`.
- Structured publication records live in `src/data/publications.yaml`.
- Course offerings live in `src/data/courses/`.
- Large downloads and self-contained artifacts live in `public/`.
- Shared layouts and components live in `src/layouts/` and `src/components/`.

For an imported post, keep `legacyPath` equal to the original Squarespace path. The page route, canonical URL, and FastComments `urlId` are all derived from it, so changing it can break inbound links and detach the historical comment thread. Copy [`templates/new-post.md`](templates/new-post.md) when starting a post.

## Deployment

The GitHub Actions workflow builds and uploads the static Astro output whenever `main` is updated. GitHub Pages serves the site at the canonical custom domain `www.daniellitt.com`; the apex domain and `chocolitt.github.io` redirect there over HTTPS. Production builds include the Google Analytics tag for `G-SQPKVD92TL`; local and pull-request preview builds do not send analytics.

The repository variable `PUBLIC_FASTCOMMENTS_TENANT_ID` supplies the public widget identifier during production builds. Preserve every existing `legacyPath`, and run `pnpm site:preview` before pushing content changes.
