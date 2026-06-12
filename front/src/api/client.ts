// Тонкий типізований HTTP-клієнт до REST API на рідному fetch (без axios).
// Базовий URL береться з env (VITE_API_BASE_URL), не хардкодиться.

import type { HealthResponse } from './types'

const baseUrl: string = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.headers ?? {}),
    },
  })

  if (!res.ok) {
    throw new Error(`HTTP ${res.status} ${res.statusText}`)
  }

  return (await res.json()) as T
}

export const api = {
  /** GET /healthz — перевірка живості бекенду. */
  getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/healthz')
  },
}
