/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly PUBLIC_FASTCOMMENTS_TENANT_ID?: string;
  readonly PUBLIC_SITE_ENV?: "preview" | "production";
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
