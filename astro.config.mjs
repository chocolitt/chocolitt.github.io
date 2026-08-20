import { defineConfig } from "astro/config";
import googleAnalytics from "./scripts/astro/google-analytics.mjs";
import preserveLegacyHtml from "./scripts/astro/preserve-legacy-html.mjs";

const isProduction = process.env.PUBLIC_SITE_ENV === "production";

export default defineConfig({
  site: "https://www.daniellitt.com",
  output: "static",
  // GitHub Pages serves directory-style routes at their trailing-slash URLs.
  // Match that behavior so Astro's route metadata never advertises a URL that
  // the production host immediately redirects.
  trailingSlash: "always",
  integrations: [
    preserveLegacyHtml(),
    googleAnalytics({ measurementId: "G-SQPKVD92TL", enabled: isProduction }),
  ],
});
