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
  type ApiJobDetail,
  type ApiJobListResponse,
  type ApiJobStatus,
  type CalendarResponse,
  type CurrentUserResponse,
  type GoogleAuthPayload,
  type HealthResponse,
  type JRIssue,
  type JRProject,
  type JRProjectPatch,
  type Period,
  type SyncTriggerResult,
  type TCProject,
  type TCProjectPatch,
  type TokenResponse,
  type UntrackedEntry,
  type UserCreate,
  type UserItem,
  type UserPatch,
  type WorklogStatus,
  type WorklogSyncTasksResponse,
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

function jsonBody(body: unknown, method: 'POST' | 'PATCH' = 'POST'): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

/** Зібрати query-string із заданих не-порожніх параметрів. */
function qs(params: Record<string, string | number | undefined>): string {
  const pairs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
  return pairs.length ? `?${pairs.join('&')}` : ''
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

  // --- Calendar (read-only тижневий timesheet) -----------------------------

  /** GET /calendar — тиждень блоків зі станом синку за період (read-only). */
  calendar(period: Period): Promise<CalendarResponse> {
    return request<CalendarResponse>(`/calendar${qs({ ...period })}`)
  },

  // --- TimeCamp ------------------------------------------------------------

  /** GET /tc-projects — проекти TimeCamp з лічильником записів за період. */
  tcProjects(period?: Period): Promise<TCProject[]> {
    return request<TCProject[]>(`/tc-projects${period ? qs({ ...period }) : ''}`)
  },

  /** PATCH /tc-projects/{id} — локальні прапори (`is_sync`, `issue_key`). */
  patchTcProject(id: number, body: TCProjectPatch): Promise<TCProject> {
    return request<TCProject>(`/tc-projects/${id}`, jsonBody(body, 'PATCH'))
  },

  /** GET /tc-entries/untracked — записи без зіставлення за період. */
  tcUntracked(period: Period): Promise<UntrackedEntry[]> {
    return request<UntrackedEntry[]>(`/tc-entries/untracked${qs({ ...period })}`)
  },

  /** POST /sync/timecamp/projects — синк проектів TimeCamp. */
  syncTcProjects(): Promise<SyncTriggerResult> {
    return request<SyncTriggerResult>('/sync/timecamp/projects', { method: 'POST' })
  },

  /** POST /sync/timecamp/entries — тягнути записи за період. */
  syncTcEntries(period: Period): Promise<SyncTriggerResult> {
    return request<SyncTriggerResult>('/sync/timecamp/entries', jsonBody(period))
  },

  // --- Jira -----------------------------------------------------------------

  /** GET /jr-projects — проекти Jira з лічильником задач. */
  jrProjects(): Promise<JRProject[]> {
    return request<JRProject[]>('/jr-projects')
  },

  /** PATCH /jr-projects/{id} — тогл `is_watched` (локальний прапор). */
  patchJrProject(id: number, body: JRProjectPatch): Promise<JRProject> {
    return request<JRProject>(`/jr-projects/${id}`, jsonBody(body, 'PATCH'))
  },

  /** GET /jr-issues — задачі Jira з локальної БД; опційний фільтр за проектом. */
  jrIssues(projectId?: number): Promise<JRIssue[]> {
    return request<JRIssue[]>(`/jr-issues${qs({ project_id: projectId })}`)
  },

  /** POST /sync/jira/projects — синк проектів Jira. */
  syncJrProjects(): Promise<SyncTriggerResult> {
    return request<SyncTriggerResult>('/sync/jira/projects', { method: 'POST' })
  },

  /** POST /sync/jira/issues — точковий синк задач за ключами. */
  syncJrIssues(keys: string[]): Promise<SyncTriggerResult> {
    return request<SyncTriggerResult>('/sync/jira/issues', jsonBody({ keys }))
  },

  // --- Tempo / worklog sync tasks ------------------------------------------

  /** GET /worklog-sync-tasks — конвеєр worklog-задач зі зведенням за період. */
  worklogSyncTasks(period: Period, status?: WorklogStatus): Promise<WorklogSyncTasksResponse> {
    return request<WorklogSyncTasksResponse>(
      `/worklog-sync-tasks${qs({ ...period, status })}`,
    )
  },

  /** POST /sync/worklog-tasks/prepare — крок `prepare` конвеєра. */
  syncWstPrepare(period: Period): Promise<SyncTriggerResult> {
    return request<SyncTriggerResult>('/sync/worklog-tasks/prepare', jsonBody(period))
  },

  /** POST /sync/worklog-tasks/resolve-issues — крок `resolve-issues`. */
  syncWstResolve(period: Period): Promise<SyncTriggerResult> {
    return request<SyncTriggerResult>(
      '/sync/worklog-tasks/resolve-issues',
      jsonBody(period),
    )
  },

  /** POST /sync/worklog-tasks/push-to-tempo — крок `push-to-tempo`. */
  syncWstPush(period: Period): Promise<SyncTriggerResult> {
    return request<SyncTriggerResult>(
      '/sync/worklog-tasks/push-to-tempo',
      jsonBody(period),
    )
  },

  // --- Sync journal (api_jobs) ---------------------------------------------

  /** GET /api-jobs — журнал sync-операцій із фільтрами. */
  apiJobs(params?: {
    status?: ApiJobStatus
    trigger_name?: string
    limit?: number
    offset?: number
  }): Promise<ApiJobListResponse> {
    return request<ApiJobListResponse>(`/api-jobs${qs({ ...params })}`)
  },

  /** GET /api-jobs/{id} — деталі job-а (payload/result/error). */
  apiJob(id: string): Promise<ApiJobDetail> {
    return request<ApiJobDetail>(`/api-jobs/${id}`)
  },

  /** POST /api-jobs/{id}/verify — підтвердити `needs_verification`. */
  verifyJob(id: string): Promise<ApiJobDetail> {
    return request<ApiJobDetail>(`/api-jobs/${id}/verify`, { method: 'POST' })
  },

  // --- Users (capability api-users-management) -----------------------------

  /** GET /users — список користувачів (без `password_hash`). */
  users(): Promise<UserItem[]> {
    return request<UserItem[]>('/users')
  },

  /** POST /users — invite без пароля (вхід через Google за e-mail). */
  createUser(body: UserCreate): Promise<UserItem> {
    return request<UserItem>('/users', jsonBody(body))
  },

  /** PATCH /users/{id} — `username` / `worker_key` / `is_active`. */
  patchUser(id: number, body: UserPatch): Promise<UserItem> {
    return request<UserItem>(`/users/${id}`, jsonBody(body, 'PATCH'))
  },

  /** DELETE /users/{id}. */
  deleteUser(id: number): Promise<void> {
    return request<void>(`/users/${id}`, { method: 'DELETE' })
  },
}
