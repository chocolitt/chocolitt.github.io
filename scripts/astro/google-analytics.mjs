import { readdir, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const GOOGLE_TAG_LOADER = "https://www.googletagmanager.com/gtag/js";

async function* htmlFiles(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const entryPath = path.join(directory, entry.name);

    if (entry.isDirectory()) {
      yield* htmlFiles(entryPath);
    } else if (entry.isFile() && entry.name.endsWith(".html")) {
      yield entryPath;
    }
  }
}

function googleTag(measurementId) {
  return `  <!-- Google tag (gtag.js) -->
  <script async src="${GOOGLE_TAG_LOADER}?id=${measurementId}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', '${measurementId}');
  </script>`;
}

export default function googleAnalytics({ measurementId, enabled }) {
  if (!/^G-[A-Z0-9]+$/.test(measurementId)) {
    throw new Error(`Invalid Google Analytics measurement ID: ${measurementId}`);
  }

  return {
    name: "google-analytics",
    hooks: {
      "astro:build:done": async ({ dir }) => {
        if (!enabled) return;

        const output = fileURLToPath(dir);

        for await (const filename of htmlFiles(output)) {
          const page = await readFile(filename, "utf8");

          if (page.includes(`${GOOGLE_TAG_LOADER}?id=${measurementId}`)) continue;
          if (page.includes(GOOGLE_TAG_LOADER)) {
            throw new Error(`A different Google tag already exists in ${filename}`);
          }

          const head = page.match(/<head(?:\s[^>]*)?>/i)?.[0];
          if (!head) throw new Error(`Cannot add Google Analytics: ${filename} has no <head>`);

          const taggedPage = page.replace(head, `${head}\n${googleTag(measurementId)}`);
          await writeFile(filename, taggedPage);
        }
      },
    },
  };
}
