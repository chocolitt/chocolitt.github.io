/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly PUBLIC_FASTCOMMENTS_TENANT_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
