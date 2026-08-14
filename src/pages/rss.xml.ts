import { getCollection } from "astro:content";
import { normalizeDescription } from "../utils/description";

export async function GET({ site }: { site: URL }) {
  const posts = (await getCollection("blog", ({ data }) => !data.draft)).sort(
    (a, b) => b.data.published.valueOf() - a.data.published.valueOf(),
  );
  const escape = (value: string) =>
    value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
  const items = posts
    .map((post) => {
      const url = new URL(post.data.legacyPath, site).href;
      const description = normalizeDescription(post.data.description, post.data.title, 320);
      return `<item><title>${escape(post.data.title)}</title><link>${url}</link><guid>${url}</guid><pubDate>${post.data.published.toUTCString()}</pubDate><description>${escape(description)}</description></item>`;
    })
    .join("");

  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Daniel Litt</title><link>${site.href}</link><description>Writing on mathematics, research, and adjacent subjects.</description>${items}</channel></rss>`,
    { headers: { "Content-Type": "application/rss+xml; charset=utf-8" } },
  );
}
