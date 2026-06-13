// Типи контрактів REST API бекенду (узгоджено з api/app/api/schemas).

export interface HealthResponse {
  status: string
}

/** Відповідь /auth/login | /auth/google | /auth/refresh. */
export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number // seconds
}

/** Відповідь GET /auth/me. */
export interface CurrentUserResponse {
  username: string
  worker_key: string | null
  expires_at: string // ISO datetime
}

/** Тіло POST /auth/google — рівно одне поле. */
export interface GoogleAuthPayload {
  credential?: string
  code?: string
}

/** Помилка API з кодом статусу і `detail` із бекенду. */
export class ApiError extends Error {
  readonly status: number
  readonly detail: string
  constructor(status: number, detail: string) {
    super(`HTTP ${status}: ${detail}`)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}
