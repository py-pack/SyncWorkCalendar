/* =========================================================================
   Sync Work — стор дані-екранів TimeCamp / Jira / Tempo. Період — поточний
   місяць (period-based endpoint-и); тогли пишуться через PATCH і оновлюють
   рядок локально; sync-тригери після успіху перезавантажують свій розділ.
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
  const tcUntracked = ref<UntrackedEntry[]>([])
  // Jira
  const jrProjects = ref<JRProject[]>([])
  const jrIssues = ref<JRIssue[]>([])
  // Tempo / worklog sync tasks
  const wst = ref<WorklogSyncTask[]>([])
  const wstSummary = ref<Record<WorklogStatus, number> | null>(null)

  const error = ref<string | null>(null)

  // ---- loaders (по екранах) ----

  /** Екран «Проекти»: обидва джерела проектів (TimeCamp + Jira). */
  async function loadProjects(): Promise<void> {
    error.value = null
    try {
      const [tc, jr] = await Promise.all([api.tcProjects(period), api.jrProjects()])
      tcProjects.value = tc
      jrProjects.value = jr
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

  /** Екран Jira: задачі + проекти Jira (потрібні для кольорового тегу задачі). */
  async function loadIssues(): Promise<void> {
    error.value = null
    try {
      const [issues, projects] = await Promise.all([api.jrIssues(), api.jrProjects()])
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

  // ---- local toggles (PATCH) ----

  async function toggleTcSync(p: TCProject): Promise<void> {
    const updated = await api.patchTcProject(p.id, { is_sync: !p.is_sync })
    tcProjects.value = tcProjects.value.map((x) => (x.id === updated.id ? updated : x))
  }

  async function toggleJrWatched(p: JRProject): Promise<void> {
    const updated = await api.patchJrProject(p.id, { is_watched: !p.is_watched })
    jrProjects.value = jrProjects.value.map((x) => (x.id === updated.id ? updated : x))
  }

  // ---- авто-синк із зовнішніх джерел при відкритті екрана ----
  // Екран спершу показує дані з БД (load*), потім у фоні тягне свіже з
  // TimeCamp/Jira і перезавантажує. Захист від флуду: не пере-синкати, якщо
  // синкали менш ніж SYNC_TTL_MS тому (швидка навігація туди-сюди).
  //
  // Кожне джерело синкається рівно з ОДНОГО екрана (D4): проекти — з «Проектів»,
  // записи — з TimeCamp, задачі — з Jira.

  // 5 хв: кожен синк створює api_jobs (needs_verification), тож не пере-синкаємо
  // частіше — дані щонайбільше 5-хв давнини, без потоку job-ів на кожну навігацію.
  const SYNC_TTL_MS = 5 * 60_000
  const lastSync = { projects: 0, entries: 0, issues: 0 }

  /** Екран «Проекти»: освіжити проекти TimeCamp + Jira. */
  async function autoSyncProjects(): Promise<void> {
    const now = Date.now()
    if (now - lastSync.projects < SYNC_TTL_MS) return
    lastSync.projects = now
    try {
      await api.syncTcProjects()
      await api.syncJrProjects()
      await loadProjects()
    } catch (e) {
      error.value = errMsg(e)
      lastSync.projects = 0 // дозволити повтор після помилки
    }
  }

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
    tcUntracked,
    jrProjects,
    jrIssues,
    wst,
    wstSummary,
    error,
    loadProjects,
    loadUntracked,
    loadIssues,
    loadTempo,
    toggleTcSync,
    toggleJrWatched,
    autoSyncProjects,
    autoSyncEntries,
    autoSyncIssues,
    syncWstPrepare,
    syncWstResolve,
    syncWstPush,
  }
})
