import { defineConfig } from "astro/config";
import preserveLegacyHtml from "./scripts/astro/preserve-legacy-html.mjs";

export default defineConfig({
  site: "https://www.daniellitt.com",
  output: "static",
  trailingSlash: "never",
  integrations: [preserveLegacyHtml()],
});
