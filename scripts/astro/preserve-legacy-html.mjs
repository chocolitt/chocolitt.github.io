import { rename, rmdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const legacyCourseFiles = [
  "mat1101.html",
  "mat1190hs.html",
  "mat445.html",
  "mat445_winter2026.html",
];

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
      },
    },
  };
}
