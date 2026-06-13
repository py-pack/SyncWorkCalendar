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

  // ---- loaders ----

  async function loadTimeCamp(): Promise<void> {
    error.value = null
    try {
      const [projects, untracked] = await Promise.all([
        api.tcProjects(period),
        api.tcUntracked(period),
      ])
      tcProjects.value = projects
      tcUntracked.value = untracked
    } catch (e) {
      error.value = errMsg(e)
    }
  }

  async function loadJira(): Promise<void> {
    error.value = null
    try {
      const [projects, issues] = await Promise.all([api.jrProjects(), api.jrIssues()])
      jrProjects.value = projects
      jrIssues.value = issues
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

  // 5 хв: кожен синк створює api_jobs (needs_verification), тож не пере-синкаємо
  // частіше — дані щонайбільше 5-хв давнини, без потоку job-ів на кожну навігацію.
  const SYNC_TTL_MS = 5 * 60_000
  const lastSync = { timecamp: 0, jira: 0 }

  async function autoSyncTimeCamp(): Promise<void> {
    const now = Date.now()
    if (now - lastSync.timecamp < SYNC_TTL_MS) return
    lastSync.timecamp = now
    try {
      await api.syncTcProjects()
      await api.syncTcEntries(sync)
      await loadTimeCamp()
    } catch (e) {
      error.value = errMsg(e)
      lastSync.timecamp = 0 // дозволити повтор після помилки
    }
  }

  async function autoSyncJira(): Promise<void> {
    const now = Date.now()
    if (now - lastSync.jira < SYNC_TTL_MS) return
    lastSync.jira = now
    try {
      // Лише проекти (легко). Задачі API синкає point-by-key (D3) — ре-синк
      // усіх відомих на кожне відкриття б'є по Jira; задачі показуємо з БД.
      await api.syncJrProjects()
      await loadJira()
    } catch (e) {
      error.value = errMsg(e)
      lastSync.jira = 0
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
    loadTimeCamp,
    loadJira,
    loadTempo,
    toggleTcSync,
    toggleJrWatched,
    autoSyncTimeCamp,
    autoSyncJira,
    syncWstPrepare,
    syncWstResolve,
    syncWstPush,
  }
})
