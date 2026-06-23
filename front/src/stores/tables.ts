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
  type Period,
  type SyncTri,
  type TCEntry,
  type TCProject,
  type TCSyncFilter,
  type WorklogStatus,
  type WorklogSyncTask,
} from '@/api/types'
import { defaultReviewPeriod, reviewPeriod, syncPeriod } from '@/lib/period'

function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.detail
  return e instanceof Error ? e.message : String(e)
}

export const useTablesStore = defineStore('tables', () => {
  // Читання — широке вікно (щоб дані показувались самі); синк — поточний місяць.
  const period = reviewPeriod()
  const sync = syncPeriod()

  // TimeCamp проекти (екран «Проекти»)
  const tcProjects = ref<TCProject[]>([])
  const tcProjectsLoaded = ref(false)
  const tcActive = ref<SyncTri>('all') // фільтр за станом синку (is_sync)
  // TimeCamp записи (екран /timecamp): читання з БД за період + фільтр стану
  // синку + серверна пагінація. Авто-синку немає — лише явна кнопка (D1).
  const TC_PAGE_SIZE = 50
  const tcEntries = ref<TCEntry[]>([])
  const tcPeriod = ref<Period>(defaultReviewPeriod()) // дефолт — «цей місяць» (D6)
  const tcSyncFilter = ref<TCSyncFilter>('all')
  const tcOffset = ref(0)
  const tcTotal = ref(0)
  const tcLoading = ref(false)
  // Jira
  const jrProjects = ref<JRProject[]>([])
  const jrProjectsLoaded = ref(false)
  const jrActive = ref<SyncTri>('all') // фільтр за станом синку (is_watched)
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

  /** Екран /timecamp: усі записи з локальної БД за поточний період/фільтр/сторінку
   *  (`GET /tc-entries`). Жодного синку — лише читання (D1). */
  async function loadTcEntries(): Promise<void> {
    error.value = null
    tcLoading.value = true
    try {
      const res = await api.tcEntries({
        start: tcPeriod.value.start,
        end: tcPeriod.value.end,
        synced: tcSyncFilter.value,
        limit: TC_PAGE_SIZE,
        offset: tcOffset.value,
      })
      tcEntries.value = res.items
      tcTotal.value = res.total
    } catch (e) {
      error.value = errMsg(e)
    } finally {
      tcLoading.value = false
    }
  }

  /** Зміна періоду перегляду → скид на першу сторінку + reload. */
  function setTcPeriod(p: Period): Promise<void> {
    tcPeriod.value = p
    tcOffset.value = 0
    return loadTcEntries()
  }

  /** Зміна фільтра стану синку → скид на першу сторінку + reload. */
  function setTcSyncFilter(f: TCSyncFilter): Promise<void> {
    tcSyncFilter.value = f
    tcOffset.value = 0
    return loadTcEntries()
  }

  /** Перехід сторінки (offset кламповано в межах [0, total)). */
  function setTcOffset(offset: number): Promise<void> {
    const max = Math.max(0, tcTotal.value - 1)
    tcOffset.value = Math.min(Math.max(0, offset), max)
    return loadTcEntries()
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

  /** Зберегти стан синку (`is_watched`) Jira-проекту з попапа (PATCH + локальне
   *  оновлення рядка). */
  async function saveJrWatched(id: number, is_watched: boolean): Promise<void> {
    const updated = await api.patchJrProject(id, { is_watched })
    jrProjects.value = jrProjects.value.map((x) => (x.id === updated.id ? updated : x))
  }

  // ---- явний синк проектів (кнопка в шапці «Проектів», ніколи не авто, D9) ----

  /** Синк проектів ОДНОГО сервісу (відповідного активній під-вʼюсі) + reload
   *  саме цього джерела. Кнопка синку синкає лише той сервіс, що зараз видно. */
  async function syncProjects(service: 'tc' | 'jr'): Promise<void> {
    error.value = null
    try {
      if (service === 'jr') {
        await api.syncJrProjects()
        await loadJrProjects({ force: true })
      } else {
        await api.syncTcProjects()
        await loadTcProjects({ force: true })
      }
    } catch (e) {
      error.value = errMsg(e)
      throw e // щоб кнопка синку показала помилку, а не «done»
    }
  }

  /** Явний синк записів TimeCamp за обраний у попапі період (ніколи не авто, D1).
   *  Після успіху перезавантажує поточну сторінку списку з локальної БД. */
  async function syncTcEntries(period: Period): Promise<void> {
    error.value = null
    try {
      await api.syncTcEntries(period)
      await loadTcEntries()
    } catch (e) {
      error.value = errMsg(e)
      throw e // щоб попап/кнопка синку показали помилку
    }
  }

  // ---- авто-синк із зовнішніх джерел при відкритті екрана ----
  // Екран спершу показує дані з БД (load*), потім у фоні тягне свіже з Jira і
  // перезавантажує. Захист від флуду: не пере-синкати, якщо синкали менш ніж
  // SYNC_TTL_MS тому (швидка навігація туди-сюди).
  //
  // Лишилось лише для задач (Jira); ПРОЕКТИ і ЗАПИСИ TimeCamp авто-синку більше
  // не мають — лише явні кнопки `syncProjects`/`syncTcEntries` (D1/D9).

  // 5 хв: кожен синк створює api_jobs (needs_verification), тож не пере-синкаємо
  // частіше — дані щонайбільше 5-хв давнини, без потоку job-ів на кожну навігацію.
  const SYNC_TTL_MS = 5 * 60_000
  const lastSync = { issues: 0 }

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
    tcEntries,
    tcPeriod,
    tcSyncFilter,
    tcOffset,
    tcTotal,
    tcLoading,
    tcPageSize: TC_PAGE_SIZE,
    jrProjects,
    jrProjectsLoaded,
    jrActive,
    jrIssues,
    wst,
    wstSummary,
    error,
    loadTcProjects,
    loadJrProjects,
    loadTcEntries,
    setTcPeriod,
    setTcSyncFilter,
    setTcOffset,
    syncTcEntries,
    loadIssues,
    loadTempo,
    saveTcSync,
    jrIssueSearch,
    saveJrWatched,
    syncProjects,
    autoSyncIssues,
    syncWstPrepare,
    syncWstResolve,
    syncWstPush,
  }
})
