// Мінімальні типи Google Identity Services (gsi/client), які ми використовуємо.
// Повний SDK не типізуємо — лише id.initialize/prompt і oauth2.initCodeClient.
export {}

interface GoogleIdConfig {
  client_id: string
  callback: (response: { credential?: string }) => void
  ux_mode?: 'popup' | 'redirect'
}

interface GoogleCodeClientConfig {
  client_id: string
  scope: string
  ux_mode?: 'popup' | 'redirect'
  callback: (response: { code?: string }) => void
}

interface GoogleCodeClient {
  requestCode: () => void
}

interface GoogleAccounts {
  id: {
    initialize: (config: GoogleIdConfig) => void
    prompt: () => void
    renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void
  }
  oauth2: {
    initCodeClient: (config: GoogleCodeClientConfig) => GoogleCodeClient
  }
}

declare global {
  interface Window {
    google?: { accounts: GoogleAccounts }
  }
}
