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
  type VerifyAllResponse,
  type CalendarResponse,
  type CurrentUserResponse,
  type GoogleAuthPayload,
  type HealthResponse,
  type JRIssuesPage,
  type JRProject,
  type JRProjectPatch,
  type JRWorklogsResponse,
  type PasswordChangePayload,
  type Period,
  type SelfUserPatch,
  type SyncPrefs,
  type SyncPrefsPatch,
  type SyncTri,
  type SyncTriggerResult,
  type TCEntriesResponse,
  type TCProject,
  type TCProjectPatch,
  type TCSyncFilter,
  type TokenResponse,
  type UntrackedEntry,
  type UserCreate,
  type UserItem,
  type UserPatch,
  type WorklogDedupResult,
  type WorklogDuplicatesResponse,
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

  /** GET /tc-projects — проекти TimeCamp (дерево + маппінг); фільтр `active`. */
  tcProjects(active?: 'active' | 'inactive' | 'all'): Promise<TCProject[]> {
    return request<TCProject[]>(`/tc-projects${qs({ active })}`)
  },

  /** PATCH /tc-projects/{id} — локальні прапори (`is_sync`, `issue_key`). */
  patchTcProject(id: number, body: TCProjectPatch): Promise<TCProject> {
    return request<TCProject>(`/tc-projects/${id}`, jsonBody(body, 'PATCH'))
  },

  /** GET /tc-entries — усі записи TimeCamp за період зі станом синку (пагінація). */
  tcEntries(params: {
    start: string
    end: string
    synced?: TCSyncFilter
    limit?: number
    offset?: number
  }): Promise<TCEntriesResponse> {
    return request<TCEntriesResponse>(
      `/tc-entries${qs({
        start: params.start,
        end: params.end,
        synced: params.synced,
        limit: params.limit,
        offset: params.offset,
      })}`,
    )
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

  /** GET /jr-issues — задачі Jira з локальної БД за період створення (пагінація).
   *  Фільтри: проект / статус / пошук; період активності `updatedFrom`/`updatedTo`. */
  jrIssues(params?: {
    projectId?: number
    status?: string
    q?: string
    updatedFrom?: string
    updatedTo?: string
    limit?: number
    offset?: number
  }): Promise<JRIssuesPage> {
    return request<JRIssuesPage>(
      `/jr-issues${qs({
        project_id: params?.projectId,
        status: params?.status,
        q: params?.q,
        updated_from: params?.updatedFrom,
        updated_to: params?.updatedTo,
        limit: params?.limit,
        offset: params?.offset,
      })}`,
    )
  },

  /** GET /jr-issues/statuses — усі наявні статуси задач (для випадайки фільтра). */
  jrIssueStatuses(): Promise<string[]> {
    return request<string[]>('/jr-issues/statuses')
  },

  /** POST /sync/jira/projects — синк проектів Jira. */
  syncJrProjects(): Promise<SyncTriggerResult> {
    return request<SyncTriggerResult>('/sync/jira/projects', { method: 'POST' })
  },

  /** POST /sync/jira/issues — точковий синк задач за ключами. */
  syncJrIssues(keys: string[]): Promise<SyncTriggerResult> {
    return request<SyncTriggerResult>('/sync/jira/issues', jsonBody({ keys }))
  },

  /** POST /sync/jira/worklogs — тягнути worklog-и за період (задачі — побічно). */
  syncJrWorklogs(period: Period): Promise<SyncTriggerResult> {
    return request<SyncTriggerResult>('/sync/jira/worklogs', jsonBody(period))
  },

  /** POST /sync/jira/issues-all — витяг задач відстежуваних проектів, активних
   *  у періоді (`updated`), незалежно від worklog-ів і assignee. */
  syncJrIssuesAll(period: Period): Promise<SyncTriggerResult> {
    return request<SyncTriggerResult>('/sync/jira/issues-all', jsonBody(period))
  },

  // --- Tempo / worklog sync tasks ------------------------------------------

  /** GET /jr-worklogs — реальні Tempo-worklog-и з БД за період (вкладка «Tempo»).
   *  `linked` (стан звʼязку з WST) + пошук `q` за назвою задачі + пагінація. */
  jrWorklogs(params: {
    start: string
    end: string
    linked?: 'all' | 'linked' | 'unlinked'
    q?: string
    limit?: number
    offset?: number
  }): Promise<JRWorklogsResponse> {
    return request<JRWorklogsResponse>(
      `/jr-worklogs${qs({
        start: params.start,
        end: params.end,
        linked: params.linked,
        q: params.q,
        limit: params.limit,
        offset: params.offset,
      })}`,
    )
  },

  /** GET /jr-worklogs/duplicates — групи дубльованих worklog-ів за період
   *  (той самий ключ дедупу, що `find_match`). Scoped по `worker_key`. */
  worklogDuplicates(period: Period): Promise<WorklogDuplicatesResponse> {
    return request<WorklogDuplicatesResponse>(`/jr-worklogs/duplicates${qs({ ...period })}`)
  },

  /** POST /jr-worklogs/dedup — масово прибрати зайві worklog-и обраних груп
   *  (реальне видалення з Tempo). `groups` — масив переліків `worklog_id`. */
  dedupWorklogs(groups: number[][]): Promise<WorklogDedupResult> {
    return request<WorklogDedupResult>(
      '/jr-worklogs/dedup',
      jsonBody({ groups: groups.map((worklog_ids) => ({ worklog_ids })) }),
    )
  },

  /** GET /worklog-sync-tasks — конвеєр worklog-задач зі зведенням за період
   *  (вкладка «Конвеєр»): фільтр стану `synced` + пошук `q` + пагінація. */
  worklogSyncTasks(params: {
    start: string
    end: string
    status?: WorklogStatus
    synced?: SyncTri
    q?: string
    limit?: number
    offset?: number
  }): Promise<WorklogSyncTasksResponse> {
    return request<WorklogSyncTasksResponse>(
      `/worklog-sync-tasks${qs({
        start: params.start,
        end: params.end,
        status: params.status,
        synced: params.synced,
        q: params.q,
        limit: params.limit,
        offset: params.offset,
      })}`,
    )
  },

  /** POST /sync/worklog-tasks/{id}/push — пуш одного WST (пер-рядкова дія). */
  pushWorklogTask(id: number): Promise<SyncTriggerResult> {
    return request<SyncTriggerResult>(`/sync/worklog-tasks/${id}/push`, { method: 'POST' })
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

  /** POST /sync/reconcile-links — реконсиляція лінків TimeCamp↔Tempo. На відміну
   *  від решти тригерів — **завжди** enqueue (capability `async-task-queue`):
   *  відповідь `202 {job_id, status:"queued"}`, без `result` і без синхронного
   *  режиму. `SyncTriggerResult` покриває обидві форми (`result` тут — `null`). */
  reconcileLinks(period: Period): Promise<SyncTriggerResult> {
    return request<SyncTriggerResult>('/sync/reconcile-links', jsonBody(period))
  },

  // --- Sync journal (api_jobs) ---------------------------------------------

  /** GET /api-jobs — журнал sync-операцій із фільтрами (статус / тригер /
   *  період за `started_at` / пагінація). */
  apiJobs(params?: {
    status?: ApiJobStatus
    trigger_name?: string
    start?: string
    end?: string
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

  /** POST /api-jobs/{id}/retry — синхронно повторити `failed`-job-у її ж
   *  параметрами. Повертає `APIJobDetail` НОВОЇ job-и (успіх → `needs_verification`,
   *  повторне падіння → `failed`; синхронна невдача — не `500`). */
  retryJob(id: string): Promise<ApiJobDetail> {
    return request<ApiJobDetail>(`/api-jobs/${id}/retry`, { method: 'POST' })
  },

  /** POST /api-jobs/verify-all — масово підтвердити `needs_verification` за
   *  поточними фільтрами (період за `started_at` + опц. `trigger_name`). */
  verifyAllJobs(params?: {
    start?: string
    end?: string
    trigger_name?: string
  }): Promise<VerifyAllResponse> {
    return request<VerifyAllResponse>(`/api-jobs/verify-all${qs({ ...params })}`, {
      method: 'POST',
    })
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

  // --- Self-service профіль (екран «Профіль») ------------------------------

  /** PATCH /users/me — self-edit власних полів (без `email`/`is_active`). */
  updateMe(body: SelfUserPatch): Promise<UserItem> {
    return request<UserItem>('/users/me', jsonBody(body, 'PATCH'))
  },

  /** PATCH /users/me/password — зміна власного пароля (хешування на беку). */
  changeMyPassword(body: PasswordChangePayload): Promise<{ status: string }> {
    return request<{ status: string }>('/users/me/password', jsonBody(body, 'PATCH'))
  },

  /** PATCH /users/me/sync-prefs — часткове оновлення перемикачів автосинку. */
  updateSyncPrefs(body: SyncPrefsPatch): Promise<SyncPrefs> {
    return request<SyncPrefs>('/users/me/sync-prefs', jsonBody(body, 'PATCH'))
  },
}
