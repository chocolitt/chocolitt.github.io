import { getCollection } from "astro:content";

export async function GET({ site }: { site: URL }) {
  const posts = await getCollection("blog", ({ data }) => !data.draft);
  const courses = await getCollection("courses");
  const pages = await getCollection("pages");
  const taxonomyPaths = posts.flatMap((post) => [
    ...post.data.tags.map((tag) => tag.path),
    ...post.data.categories.map((category) => category.path),
  ]);
  const paths = [...new Set([
    "/",
    "/blog",
    "/work",
    "/search",
    "/teaching",
    "/artifacts",
    "/fermat_fano_real_mesh_web.html",
    "/published-paper-reviews.html",
    ...posts.map((post) => post.data.legacyPath),
    ...pages.map((page) => page.data.legacyPath),
    ...taxonomyPaths,
    ...courses.map((course) => course.data.legacyPath),
  ])];
  const urls = paths.map((path) => `<url><loc>${new URL(path, site).href}</loc></url>`).join("");
  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`,
    { headers: { "Content-Type": "application/xml; charset=utf-8" } },
  );
}
