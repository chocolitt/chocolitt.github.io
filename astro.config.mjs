import { defineConfig } from "astro/config";
import googleAnalytics from "./scripts/astro/google-analytics.mjs";
import preserveLegacyHtml from "./scripts/astro/preserve-legacy-html.mjs";

const isProduction = process.env.PUBLIC_SITE_ENV === "production";

export default defineConfig({
  site: "https://www.daniellitt.com",
  output: "static",
  trailingSlash: "never",
  integrations: [
    preserveLegacyHtml(),
    googleAnalytics({ measurementId: "G-SQPKVD92TL", enabled: isProduction }),
  ],
});
