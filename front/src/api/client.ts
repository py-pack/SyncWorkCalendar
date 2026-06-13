// Тонкий типізований HTTP-клієнт до REST API на рідному fetch (без axios).
// Базовий URL береться з env (VITE_API_BASE_URL), не хардкодиться.
//
// Авторизація — через інверсію залежностей (як і onUnauthorized): клієнт НЕ
// знає ні про store, ні про storage. main.ts реєструє:
//   • tokenProvider — синхронно віддає АКТУАЛЬНИЙ токен (жива ref зі store);
//   • onUnauthorized — реакція на 401.
// Завдяки цьому токен у запиті завжди дорівнює поточному значенню в пам'яті —
// без проміжного персисту/мікротасків, тож гонка «токен ще не доїхав» (login
// → /auth/me) структурно неможлива.
//
// Запити авторизовані ЗА ЗАМОВЧУВАННЯМ. Публічні ендпоінти явно позначаються
// { public: true } — новий метод неможливо випадково лишити без Authorization.

import {
  ApiError,
  type CurrentUserResponse,
  type GoogleAuthPayload,
  type HealthResponse,
  type TokenResponse,
} from './types'

const baseUrl: string = import.meta.env.VITE_API_BASE_URL ?? ''

// --- Інверсія залежностей (wiring у main.ts) -------------------------------

let tokenProvider: () => string | null = () => null
/** Зареєструвати джерело актуального токена (жива ref зі auth-store). */
export function setTokenProvider(fn: () => string | null): void {
  tokenProvider = fn
}

// 401 на authed-запиті піднімає цей хук (main.ts вішає на auth.logout()),
// щоб клієнт лишався без залежності від Pinia-сторів.
let onUnauthorized: (() => void) | null = null
export function setUnauthorizedHandler(fn: () => void): void {
  onUnauthorized = fn
}

interface RequestOpts {
  public?: boolean // публічний ендпоінт — НЕ підкладати Authorization
}

async function request<T>(path: string, init?: RequestInit, opts?: RequestOpts): Promise<T> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...((init?.headers as Record<string, string>) ?? {}),
  }

  const requiresAuth = !opts?.public
  if (requiresAuth) {
    const token = tokenProvider()
    if (!token) {
      // Захищений запит без токена — не б'ємо сервер даремно, одразу 401.
      onUnauthorized?.()
      throw new ApiError(401, 'Not authenticated')
    }
    headers.Authorization = `Bearer ${token}`
  }

  const res = await fetch(`${baseUrl}${path}`, { ...init, headers })

  if (res.status === 401 && requiresAuth) {
    onUnauthorized?.()
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = (await res.json()) as { detail?: string }
      if (body?.detail) detail = body.detail
    } catch {
      /* тіло не JSON — лишаємо дефолтний detail */
    }
    throw new ApiError(res.status, detail)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

function jsonBody(body: unknown): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

/** Опт-аут з авторизації — лише для справді публічних ендпоінтів. */
const PUBLIC: RequestOpts = { public: true }

export const api = {
  /** GET /healthz — перевірка живості бекенду (публічний). */
  getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/healthz', undefined, PUBLIC)
  },

  /** POST /auth/login — логін/пароль (публічний). */
  login(username: string, password: string): Promise<TokenResponse> {
    return request<TokenResponse>('/auth/login', jsonBody({ username, password }), PUBLIC)
  },

  /** POST /auth/google — Google credential (One Tap) або code (popup), публічний. */
  google(payload: GoogleAuthPayload): Promise<TokenResponse> {
    return request<TokenResponse>('/auth/google', jsonBody(payload), PUBLIC)
  },

  /** POST /auth/refresh — оновити токен (авторизований). */
  refresh(): Promise<TokenResponse> {
    return request<TokenResponse>('/auth/refresh', { method: 'POST' })
  },

  /** GET /auth/me — поточний користувач (авторизований). */
  me(): Promise<CurrentUserResponse> {
    return request<CurrentUserResponse>('/auth/me')
  },
}
