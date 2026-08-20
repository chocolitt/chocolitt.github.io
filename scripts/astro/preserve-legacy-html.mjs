import { readdir, readFile, rename, rmdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const legacyCourseFiles = [
  "mat1101.html",
  "mat1190hs.html",
  "mat445.html",
  "mat445_winter2026.html",
];

async function findHtmlFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(entries.map(async (entry) => {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) return findHtmlFiles(absolute);
    return entry.isFile() && entry.name.endsWith(".html") ? [absolute] : [];
  }));
  return nested.flat();
}

function routeForIndex(output, filename) {
  const relativeDirectory = path.relative(output, path.dirname(filename)).split(path.sep).join("/");
  return relativeDirectory ? `/${relativeDirectory}/` : "/";
}

function normalizeNavigationUrl(value, directoryRoutes) {
  if (!value.startsWith("/") || value.startsWith("//")) return value;

  const suffixIndex = value.search(/[?#]/);
  const pathname = suffixIndex === -1 ? value : value.slice(0, suffixIndex);
  const suffix = suffixIndex === -1 ? "" : value.slice(suffixIndex);
  if (pathname.endsWith("/")) return value;

  const normalized = `${pathname}/`;
  return directoryRoutes.has(normalized) ? `${normalized}${suffix}` : value;
}

async function normalizeNavigationLinks(output) {
  const htmlFiles = await findHtmlFiles(output);
  const directoryRoutes = new Set(
    htmlFiles
      .filter((filename) => path.basename(filename) === "index.html")
      .map((filename) => routeForIndex(output, filename)),
  );

  for (const filename of htmlFiles) {
    const source = await readFile(filename, "utf8");
    const normalized = source.replace(
      /(\s(?:href|action)=)(["'])([^"']+)\2/gi,
      (_match, attribute, quote, value) =>
        `${attribute}${quote}${normalizeNavigationUrl(value, directoryRoutes)}${quote}`,
    );
    if (normalized !== source) await writeFile(filename, normalized);
  }
}

export default function preserveLegacyHtml() {
  return {
    name: "preserve-legacy-html",
    hooks: {
      "astro:build:done": async ({ dir }) => {
        const output = fileURLToPath(dir);

        for (const filename of legacyCourseFiles) {
          const generatedDirectory = path.join(output, filename);
          const generatedPage = path.join(generatedDirectory, "index.html");
          const temporaryPage = path.join(output, `.${filename}.tmp`);

          await rename(generatedPage, temporaryPage);
          await rmdir(generatedDirectory);
          await rename(temporaryPage, path.join(output, filename));
        }

        // Source content intentionally retains the original Squarespace paths
        // for migration fidelity and stable comment IDs. Rewrite only rendered
        // navigation URLs so visitors and crawlers go directly to the URLs that
        // GitHub Pages serves without a redirect.
        await normalizeNavigationLinks(output);
      },
    },
  };
}
