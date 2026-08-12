# daniellitt.com

Astro source for the in-progress migration of `www.daniellitt.com`. Production is still served by the existing Squarespace and GitHub Pages sites; do not merge this branch or change DNS until the migration acceptance gates pass.

## Local development

Requires Node.js 22.12 or newer and pnpm.

```sh
pnpm install --frozen-lockfile
cp .env.example .env
pnpm dev
```

Set `PUBLIC_FASTCOMMENTS_TENANT_ID` in `.env` to load the real comment widget. The value is a public browser identifier, but the local environment file remains ignored so preview configuration is not committed accidentally.

Run the complete static checks with:

```sh
pnpm build
python3 scripts/validation/check_build.py dist
```

## Content

- Blog posts live in `src/data/blog/`.
- Course offerings live in `src/data/courses/`.
- Large downloads and self-contained artifacts live in `public/`.
- Shared layouts and components live in `src/layouts/` and `src/components/`.

For an imported post, keep `legacyPath` equal to the original Squarespace path. The page route, canonical URL, and FastComments `urlId` are all derived from it, so changing it can break inbound links and detach the historical comment thread.

The one-post WXR converter can be run as follows:

```sh
python3 scripts/migration/convert_wxr_post.py \
  /path/to/export.xml \
  /blog/YYYY/M/D/post-slug \
  src/data/blog/post-slug.md \
  --description "A short page description."
```

Generated Markdown and image captions must be reviewed before commit. The current converter includes the asset mappings needed for the Library of Babel milestone post; the mapping should be generalized before full-archive conversion.

## Deployment

The GitHub Actions workflow builds and uploads the static Astro output when `main` is updated. Before the first deployment, configure the repository variable `PUBLIC_FASTCOMMENTS_TENANT_ID`, select GitHub Actions as the Pages source, and follow the staged launch plan. The custom-domain `CNAME` file and DNS cutover are deliberately deferred to the launch phase.
