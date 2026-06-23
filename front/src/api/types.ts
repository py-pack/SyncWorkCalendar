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

// --- Дані-екрани (capability frontend-data-tables / sync-journal / users) ---

/** Період запиту (ISO `yyyy-mm-dd`) для period-based endpoint-ів. */
export interface Period {
  start: string
  end: string
}

/** Статуси worklog-sync-task (= `StatusTaskEnum`). */
export type WorklogStatus =
  | 'pre_create'
  | 'create'
  | 'created'
  | 'pre_update'
  | 'update'
  | 'updated'
  | 'sync'

/** Статуси `api_jobs` (= `APIJobStatusEnum`). */
export type ApiJobStatus = 'running' | 'needs_verification' | 'verified' | 'failed'

/** Відповідь не-background sync-тригера (`POST /sync/**`). */
export interface SyncTriggerResult {
  job_id: string
  status: string
  result: Record<string, unknown> | null
}

// TimeCamp ------------------------------------------------------------------

export interface TCProject {
  id: number
  name: string
  parent_id: number | null
  color: string | null
  is_archived: boolean
  is_sync: boolean
  issue_key: string | null
  /** Назва змапованої Jira-задачі (резолв на беку); null — не змаплено/не знайдено. */
  issue_name: string | null
  /** Статус задачі не в «done»-сеті; null — issue_name не резолвнуто. */
  issue_active: boolean | null
}

export interface TCProjectPatch {
  is_sync?: boolean
  issue_key?: string
}

export interface UntrackedEntry {
  id: number
  description: string | null
  start_at: string
  end_at: string
  tc_project_id: number | null
  tc_project_name: string | null
}

/** Канонічний tri-стан синку — спільний для ВСІХ дані-екранів (фільтр + стор).
 *  Один тип живить `SyncFilter`/`SyncState` і поля `tcActive`/`jrActive`/
 *  `tcSyncFilter`, щоб «мова синку» була однакова скрізь. */
export type SyncTri = 'all' | 'synced' | 'unsynced'

/** Фільтр стану синку для `GET /tc-entries` (= канонічний `SyncTri`). */
export type TCSyncFilter = SyncTri

/** Рядок списку `GET /tc-entries`: запис TimeCamp із похідним станом синку. */
export interface TCEntry {
  id: number
  description: string | null
  start_at: string
  end_at: string
  tc_project_id: number | null
  tc_project_name: string | null
  issue_key: string | null
  is_synced: boolean
}

/** Сторінкована відповідь `GET /tc-entries`. */
export interface TCEntriesResponse {
  items: TCEntry[]
  total: number
}

// Jira ----------------------------------------------------------------------

export interface JRProject {
  id: number
  key: string
  name: string
  is_archived: boolean
  is_watched: boolean
  issues_count: number
}

export interface JRProjectPatch {
  is_watched?: boolean
}

export interface JRIssue {
  id: number
  key: string
  name: string
  jr_project_id: number
  type: string
  priority: string
  status: string
  /** Похідне: статус не в «done»-сеті (для тьмяності закритих задач). */
  active: boolean
  epic_key: string | null
  parent_key: string | null
  estimate_plan: number
  estimate_fact: number
  estimate_rest: number
}

// Tempo / worklog sync tasks ------------------------------------------------

export interface WorklogSyncTask {
  id: number
  status: WorklogStatus
  source_id: number
  target_id: number | null
  worker_key: string
  issue_key: string
  issue_id: number | null
  content: string | null
  started_at: string
  time_spent: number
}

export interface WorklogSyncTasksResponse {
  summary: Record<WorklogStatus, number>
  items: WorklogSyncTask[]
}

// Calendar (capability api-calendar / frontend-calendar) --------------------

/** Стан блоку календаря (проекція `StatusTaskEnum`). Бекенд віддає лише ці
 *  три; `failed` — суто фронтовий error-стиль (forward-compat, не з бекенда). */
export type CalendarStatus = 'service' | 'tempo' | 'synced'

/** Проект блоку — джерело кольору і назви. */
export interface CalendarProject {
  key: string | null
  name: string | null
  color: string | null
}

/** Один блок робочого часу (read-проекція tc_entry ⋈ WST ⋈ tc_project). */
export interface CalendarBlock {
  id: number
  start: string // ISO datetime
  end: string // ISO datetime
  issue_key: string | null
  description: string | null
  status: CalendarStatus
  project: CalendarProject
}

/** Відповідь GET /calendar — тиждень блоків. */
export interface CalendarResponse {
  blocks: CalendarBlock[]
}

// Sync journal (api_jobs) ---------------------------------------------------

export interface ApiJobSummary {
  id: string
  trigger_name: string
  status: ApiJobStatus
  created_by: string
  verified_by: string | null
  started_at: string
  finished_at: string | null
  verified_at: string | null
}

export interface ApiJobDetail extends ApiJobSummary {
  payload: Record<string, unknown> | null
  result: Record<string, unknown> | null
  error: string | null
}

export interface ApiJobListResponse {
  items: ApiJobSummary[]
  total: number
}

// Users ---------------------------------------------------------------------

export interface UserItem {
  id: number
  username: string
  email: string | null
  worker_key: string | null
  is_active: boolean
}

export interface UserCreate {
  username: string
  email: string
  worker_key?: string | null
  password?: string | null
}

export interface UserPatch {
  username?: string
  worker_key?: string | null
  is_active?: boolean
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
