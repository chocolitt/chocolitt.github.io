# daniellitt.com

Astro source for the in-progress migration of `www.daniellitt.com`. Production is still served by the existing Squarespace and GitHub Pages sites; do not merge this branch or change DNS until the migration acceptance gates pass.

## Preview

Requires Node.js 22.12 or newer and pnpm.

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

## Content

- Blog posts live in `src/data/blog/`.
- Ordinary Squarespace pages live in `src/data/pages/`.
- Structured publication records live in `src/data/publications.yaml`.
- Course offerings live in `src/data/courses/`.
- Large downloads and self-contained artifacts live in `public/`.
- Shared layouts and components live in `src/layouts/` and `src/components/`.

For an imported post, keep `legacyPath` equal to the original Squarespace path. The page route, canonical URL, and FastComments `urlId` are all derived from it, so changing it can break inbound links and detach the historical comment thread. Copy [`templates/new-post.md`](templates/new-post.md) when starting a post.

## Deployment

The GitHub Actions workflow builds and uploads the static Astro output when `main` is updated. Before the first deployment, configure the repository variable `PUBLIC_FASTCOMMENTS_TENANT_ID`, select GitHub Actions as the Pages source, and follow the staged launch plan. The custom-domain `CNAME` file and DNS cutover are deliberately deferred to the launch phase.
