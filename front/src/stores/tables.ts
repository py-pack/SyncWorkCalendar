/* =========================================================================
   Sync Work — стор дані-екранів TimeCamp / Jira / Tempo. Записи/Tempo —
   period-based (поточний місяць); ПРОЕКТИ — без періоду, кожна під-вʼюха
   вантажить власні дані одним запитом, ідемпотентно (rework-projects-screen).
   Тогли/налаштування пишуться через PATCH і оновлюють рядок локально;
   sync-тригери після успіху перезавантажують свій розділ.
   ========================================================================= */
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api } from '@/api/client'
import {
  ApiError,
  type JRIssue,
  type JRProject,
  type TCProject,
  type UntrackedEntry,
  type WorklogStatus,
  type WorklogSyncTask,
} from '@/api/types'
import { reviewPeriod, syncPeriod } from '@/lib/period'

function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.detail
  return e instanceof Error ? e.message : String(e)
}

export const useTablesStore = defineStore('tables', () => {
  // Читання — широке вікно (щоб дані показувались самі); синк — поточний місяць.
  const period = reviewPeriod()
  const sync = syncPeriod()

  // TimeCamp
  const tcProjects = ref<TCProject[]>([])
  const tcProjectsLoaded = ref(false)
  const tcActive = ref<'active' | 'inactive' | 'all'>('all')
  const tcUntracked = ref<UntrackedEntry[]>([])
  // Jira
  const jrProjects = ref<JRProject[]>([])
  const jrProjectsLoaded = ref(false)
  const jrIssues = ref<JRIssue[]>([])
  // Tempo / worklog sync tasks
  const wst = ref<WorklogSyncTask[]>([])
  const wstSummary = ref<Record<WorklogStatus, number> | null>(null)

  const error = ref<string | null>(null)

  // ---- loaders (по екранах) ----

  // Під-вʼюхи «Проектів» вантажать СВОЄ джерело окремо, по одному запиту
  // (D10). Кожен loader ідемпотентний (guard за `*Loaded`), щоб перемикання
  // вкладок туди-сюди не пере-запитувало; `force` — для явного синку/фільтра.

  /** Під-вʼюха TimeCamp: лише `GET /tc-projects` (усі проекти одним запитом).
   *  Фільтр `tcActive` (за `is_sync`) застосовується на клієнті — без re-fetch. */
  async function loadTcProjects(opts?: { force?: boolean }): Promise<void> {
    if (tcProjectsLoaded.value && !opts?.force) return
    error.value = null
    try {
      tcProjects.value = await api.tcProjects()
      tcProjectsLoaded.value = true
    } catch (e) {
      error.value = errMsg(e)
    }
  }

  /** Під-вʼюха Jira: лише `GET /jr-projects` (тягнеться при відкритті вкладки). */
  async function loadJrProjects(opts?: { force?: boolean }): Promise<void> {
    if (jrProjectsLoaded.value && !opts?.force) return
    error.value = null
    try {
      jrProjects.value = await api.jrProjects()
      jrProjectsLoaded.value = true
    } catch (e) {
      error.value = errMsg(e)
    }
  }

  /** Екран TimeCamp: лише незіставлені записи. */
  async function loadUntracked(): Promise<void> {
    error.value = null
    try {
      tcUntracked.value = await api.tcUntracked(period)
    } catch (e) {
      error.value = errMsg(e)
    }
  }

  /** Екран Jira: задачі + проекти Jira (потрібні для кольорового тегу задачі).
   *  `limit: 50` — стеля контракту `/jr-issues` (дефолт 10 — для select-а). */
  async function loadIssues(): Promise<void> {
    error.value = null
    try {
      const [issues, projects] = await Promise.all([
        api.jrIssues({ limit: 50 }),
        api.jrProjects(),
      ])
      jrIssues.value = issues
      jrProjects.value = projects
    } catch (e) {
      error.value = errMsg(e)
    }
  }

  async function loadTempo(): Promise<void> {
    error.value = null
    try {
      const res = await api.worklogSyncTasks(period)
      wst.value = res.items
      wstSummary.value = res.summary
    } catch (e) {
      error.value = errMsg(e)
    }
  }

  // ---- local writes (PATCH) ----

  /** Зберегти налаштування синку TC-проекту з попапа (PATCH + локальне оновлення).
   *  PATCH повертає повний шейп (з резолвом `issue_name`), тож рядок замінюємо. */
  async function saveTcSync(
    id: number,
    patch: { is_sync: boolean; issue_key?: string },
  ): Promise<void> {
    const updated = await api.patchTcProject(id, patch)
    tcProjects.value = tcProjects.value.map((x) => (x.id === updated.id ? updated : x))
  }

  /** Пошук задач для select-а в попапі (до 10, з похідним `active`). */
  function jrIssueSearch(q: string): Promise<JRIssue[]> {
    return api.jrIssues({ q, limit: 10 })
  }

  async function toggleJrWatched(p: JRProject): Promise<void> {
    const updated = await api.patchJrProject(p.id, { is_watched: !p.is_watched })
    jrProjects.value = jrProjects.value.map((x) => (x.id === updated.id ? updated : x))
  }

  // ---- явний синк проектів (кнопка в шапці «Проектів», ніколи не авто, D9) ----

  /** Синк проектів для КОЖНОГО сервісу незалежно (TimeCamp + Jira), потім reload
   *  завантажених джерел. `allSettled` — щоб збій одного сервісу не блокував інший. */
  async function syncProjects(): Promise<void> {
    error.value = null
    const results = await Promise.allSettled([api.syncTcProjects(), api.syncJrProjects()])

    const tasks: Promise<void>[] = []
    if (tcProjectsLoaded.value) tasks.push(loadTcProjects({ force: true }))
    if (jrProjectsLoaded.value) tasks.push(loadJrProjects({ force: true }))
    await Promise.all(tasks)

    const failed = results.find((r) => r.status === 'rejected')
    if (failed) {
      const reason = (failed as PromiseRejectedResult).reason
      error.value = errMsg(reason)
      throw reason // щоб кнопка синку показала помилку, а не «done»
    }
  }

  // ---- авто-синк із зовнішніх джерел при відкритті екрана ----
  // Екран спершу показує дані з БД (load*), потім у фоні тягне свіже з
  // TimeCamp/Jira і перезавантажує. Захист від флуду: не пере-синкати, якщо
  // синкали менш ніж SYNC_TTL_MS тому (швидка навігація туди-сюди).
  //
  // Лишилось для записів (TimeCamp) і задач (Jira); ПРОЕКТИ авто-синку більше
  // не мають — лише явна кнопка `syncProjects` (D9).

  // 5 хв: кожен синк створює api_jobs (needs_verification), тож не пере-синкаємо
  // частіше — дані щонайбільше 5-хв давнини, без потоку job-ів на кожну навігацію.
  const SYNC_TTL_MS = 5 * 60_000
  const lastSync = { entries: 0, issues: 0 }

  /** Екран TimeCamp: освіжити записи за період. */
  async function autoSyncEntries(): Promise<void> {
    const now = Date.now()
    if (now - lastSync.entries < SYNC_TTL_MS) return
    lastSync.entries = now
    try {
      await api.syncTcEntries(sync)
      await loadUntracked()
    } catch (e) {
      error.value = errMsg(e)
      lastSync.entries = 0
    }
  }

  /** Екран Jira: re-sync відомих ключів задач (API лише point-by-key, D3). */
  async function autoSyncIssues(): Promise<void> {
    const now = Date.now()
    if (now - lastSync.issues < SYNC_TTL_MS) return
    lastSync.issues = now
    try {
      const keys = jrIssues.value.map((i) => i.key)
      if (keys.length) await api.syncJrIssues(keys)
      await loadIssues()
    } catch (e) {
      error.value = errMsg(e)
      lastSync.issues = 0
    }
  }

  // ---- Tempo pipeline (ручні дії — мутують Tempo, авто НЕ запускаємо) ----

  async function syncWstPrepare(): Promise<void> {
    await api.syncWstPrepare(sync)
    await loadTempo()
  }
  async function syncWstResolve(): Promise<void> {
    await api.syncWstResolve(sync)
    await loadTempo()
  }
  /** «Синхронізувати вибрані» мапиться на period-based push (D4 / Q1). */
  async function syncWstPush(): Promise<void> {
    await api.syncWstPush(sync)
    await loadTempo()
  }

  return {
    period,
    tcProjects,
    tcProjectsLoaded,
    tcActive,
    tcUntracked,
    jrProjects,
    jrProjectsLoaded,
    jrIssues,
    wst,
    wstSummary,
    error,
    loadTcProjects,
    loadJrProjects,
    loadUntracked,
    loadIssues,
    loadTempo,
    saveTcSync,
    jrIssueSearch,
    toggleJrWatched,
    syncProjects,
    autoSyncEntries,
    autoSyncIssues,
    syncWstPrepare,
    syncWstResolve,
    syncWstPush,
  }
})
