/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Базовий префікс REST API (напр. `/api`). Проксується Vite у dev. */
  readonly VITE_API_BASE_URL: string
  /** Публічний Google OAuth client_id (One Tap / popup). Порожній = вимкнено. */
  readonly VITE_GOOGLE_CLIENT_ID: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<Record<string, never>, Record<string, never>, unknown>
  export default component
}
