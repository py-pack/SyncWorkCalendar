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
  type JRWorklog,
  type Period,
  type SyncTri,
  type TCEntry,
  type TCProject,
  type TCSyncFilter,
  type WorklogStatus,
  type WorklogSyncTask,
} from '@/api/types'
import { defaultIssuePeriod, defaultReviewPeriod } from '@/lib/period'

/** SyncTri (вкладка «Tempo») → параметр `linked` ендпоінта `/jr-worklogs`. */
function linkedParam(tri: SyncTri): 'all' | 'linked' | 'unlinked' {
  return tri === 'synced' ? 'linked' : tri === 'unsynced' ? 'unlinked' : 'all'
}

function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.detail
  return e instanceof Error ? e.message : String(e)
}

export const useTablesStore = defineStore('tables', () => {
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
  // Jira проекти (екран «Проекти»)
  const jrProjects = ref<JRProject[]>([])
  const jrProjectsLoaded = ref(false)
  const jrActive = ref<SyncTri>('all') // фільтр за станом синку (is_watched)
  // Jira задачі (екран /jira): читання з БД за період СТВОРЕННЯ + фільтри
  // (проект / статус / пошук) + серверна пагінація. Авто-синку немає — лише
  // явна кнопка (rework-jira-issues-screen, D1).
  const JR_PAGE_SIZE = 50
  const jrIssues = ref<JRIssue[]>([])
  const jrPeriod = ref<Period>(defaultIssuePeriod()) // дефолт — «цей рік» (фідбек QA)
  const jrStatus = ref<string | null>(null)
  const jrProjectFilter = ref<number | null>(null)
  const jrQuery = ref('')
  const jrOffset = ref(0)
  const jrTotal = ref(0)
  const jrLoading = ref(false)
  const jrStatusOptions = ref<string[]>([]) // наповнюється раз із /jr-issues/statuses
  const jrStatusLoaded = ref(false)
  // Tempo screen — спільний розмір сторінки обох вкладок.
  const TEMPO_PAGE_SIZE = 50
  // Вкладка «Tempo»: реальні Tempo-worklog-и (`GET /jr-worklogs`); стан синку =
  // звʼязаний із нашим WST (`is_linked`). Читання з БД + явна дія «Забрати з Tempo».
  const jrWorklogs = ref<JRWorklog[]>([])
  const tempoPeriod = ref<Period>(defaultReviewPeriod())
  const tempoLinkFilter = ref<SyncTri>('all')
  const tempoQuery = ref('')
  const tempoOffset = ref(0)
  const tempoTotal = ref(0)
  const tempoLoading = ref(false)
  // Вкладка «Конвеєр»: `worklog_sync_tasks` (`GET /worklog-sync-tasks`); стан
  // синку = запушено в Tempo (`target_id`). Пер-рядковий пуш замість чекбоксів.
  const wst = ref<WorklogSyncTask[]>([])
  const wstSummary = ref<Record<WorklogStatus, number> | null>(null)
  const wstPeriod = ref<Period>(defaultReviewPeriod())
  const wstSyncFilter = ref<SyncTri>('all')
  const wstQuery = ref('')
  const wstOffset = ref(0)
  const wstTotal = ref(0)
  const wstLoading = ref(false)

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

  /** Випадайка статусів — наповнюється раз (усі наявні статуси з БД).
   *  Помилка не блокує екран (випадайка просто лишиться порожньою). */
  async function loadJrStatuses(): Promise<void> {
    if (jrStatusLoaded.value) return
    try {
      jrStatusOptions.value = await api.jrIssueStatuses()
      jrStatusLoaded.value = true
    } catch {
      /* випадайка статусів лишиться порожньою — таблицю не блокуємо */
    }
  }

  /** Екран /jira: задачі з локальної БД за поточний період/фільтри/сторінку
   *  (`GET /jr-issues`). Жодного синку — лише читання (D1). Випадайки проекту й
   *  статусу наповнюються раз, паралельно з першою сторінкою. */
  async function loadJrIssues(): Promise<void> {
    error.value = null
    jrLoading.value = true
    if (!jrProjectsLoaded.value) void loadJrProjects()
    if (!jrStatusLoaded.value) void loadJrStatuses()
    try {
      const res = await api.jrIssues({
        updatedFrom: jrPeriod.value.start,
        updatedTo: jrPeriod.value.end,
        projectId: jrProjectFilter.value ?? undefined,
        status: jrStatus.value ?? undefined,
        q: jrQuery.value || undefined,
        limit: JR_PAGE_SIZE,
        offset: jrOffset.value,
      })
      jrIssues.value = res.items
      jrTotal.value = res.total
    } catch (e) {
      error.value = errMsg(e)
    } finally {
      jrLoading.value = false
    }
  }

  /** Зміна періоду створення → скид на першу сторінку + reload. */
  function setJrPeriod(p: Period): Promise<void> {
    jrPeriod.value = p
    jrOffset.value = 0
    return loadJrIssues()
  }

  /** Зміна фільтра статусу (`null` — усі) → скид на першу сторінку + reload. */
  function setJrStatus(s: string | null): Promise<void> {
    jrStatus.value = s
    jrOffset.value = 0
    return loadJrIssues()
  }

  /** Зміна фільтра проекту (`null` — усі) → скид на першу сторінку + reload. */
  function setJrProjectFilter(id: number | null): Promise<void> {
    jrProjectFilter.value = id
    jrOffset.value = 0
    return loadJrIssues()
  }

  /** Зміна пошуку за назвою → скид на першу сторінку + reload. */
  function setJrQuery(q: string): Promise<void> {
    jrQuery.value = q
    jrOffset.value = 0
    return loadJrIssues()
  }

  /** Перехід сторінки (offset кламповано в межах [0, total)). */
  function setJrOffset(offset: number): Promise<void> {
    const max = Math.max(0, jrTotal.value - 1)
    jrOffset.value = Math.min(Math.max(0, offset), max)
    return loadJrIssues()
  }

  // ---- Tempo: вкладка «Tempo» (реальні jr_worklogs, read з БД) ----

  /** Вкладка «Tempo»: реальні Tempo-worklog-и за період/фільтр/сторінку
   *  (`GET /jr-worklogs`). Лише читання — синк окремою дією «Забрати з Tempo». */
  async function loadJrWorklogs(): Promise<void> {
    error.value = null
    tempoLoading.value = true
    try {
      const res = await api.jrWorklogs({
        start: tempoPeriod.value.start,
        end: tempoPeriod.value.end,
        linked: linkedParam(tempoLinkFilter.value),
        q: tempoQuery.value || undefined,
        limit: TEMPO_PAGE_SIZE,
        offset: tempoOffset.value,
      })
      jrWorklogs.value = res.items
      tempoTotal.value = res.total
    } catch (e) {
      error.value = errMsg(e)
    } finally {
      tempoLoading.value = false
    }
  }

  function setTempoPeriod(p: Period): Promise<void> {
    tempoPeriod.value = p
    tempoOffset.value = 0
    return loadJrWorklogs()
  }
  function setTempoLinkFilter(f: SyncTri): Promise<void> {
    tempoLinkFilter.value = f
    tempoOffset.value = 0
    return loadJrWorklogs()
  }
  function setTempoQuery(q: string): Promise<void> {
    tempoQuery.value = q
    tempoOffset.value = 0
    return loadJrWorklogs()
  }
  function setTempoOffset(offset: number): Promise<void> {
    const max = Math.max(0, tempoTotal.value - 1)
    tempoOffset.value = Math.min(Math.max(0, offset), max)
    return loadJrWorklogs()
  }

  /** «Забрати з Tempo» — тягне `jr_worklogs` із сервера за період і перечитує
   *  вкладку з БД (`POST /sync/jira/worklogs` → `GET /jr-worklogs`). */
  async function syncJrWorklogs(period: Period): Promise<void> {
    error.value = null
    try {
      await api.syncJrWorklogs(period)
      await loadJrWorklogs()
    } catch (e) {
      error.value = errMsg(e)
      throw e // щоб попап синку показав помилку
    }
  }

  // ---- Tempo: вкладка «Конвеєр» (worklog_sync_tasks) ----

  /** Вкладка «Конвеєр»: WST за період/фільтр стану/сторінку
   *  (`GET /worklog-sync-tasks`). `summary` — по всьому періоду. */
  async function loadWst(): Promise<void> {
    error.value = null
    wstLoading.value = true
    try {
      const res = await api.worklogSyncTasks({
        start: wstPeriod.value.start,
        end: wstPeriod.value.end,
        synced: wstSyncFilter.value,
        q: wstQuery.value || undefined,
        limit: TEMPO_PAGE_SIZE,
        offset: wstOffset.value,
      })
      wst.value = res.items
      wstSummary.value = res.summary
      wstTotal.value = res.total
    } catch (e) {
      error.value = errMsg(e)
    } finally {
      wstLoading.value = false
    }
  }

  function setWstPeriod(p: Period): Promise<void> {
    wstPeriod.value = p
    wstOffset.value = 0
    return loadWst()
  }
  function setWstSyncFilter(f: SyncTri): Promise<void> {
    wstSyncFilter.value = f
    wstOffset.value = 0
    return loadWst()
  }
  function setWstQuery(q: string): Promise<void> {
    wstQuery.value = q
    wstOffset.value = 0
    return loadWst()
  }
  function setWstOffset(offset: number): Promise<void> {
    const max = Math.max(0, wstTotal.value - 1)
    wstOffset.value = Math.min(Math.max(0, offset), max)
    return loadWst()
  }

  /** Пер-рядковий пуш одного WST у Tempo (`POST /sync/worklog-tasks/{id}/push`)
   *  + reload конвеєра. Помилку кидає, щоб кнопка рядка показала стан. */
  async function pushOneWst(id: number): Promise<void> {
    error.value = null
    try {
      await api.pushWorklogTask(id)
      await loadWst()
    } catch (e) {
      error.value = errMsg(e)
      throw e
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

  /** Пошук задач для select-а мапінгу (до 10, з похідним `active`).
   *  `GET /jr-issues` дефолтиться на поточний місяць — для мапінгу шукаємо
   *  серед УСІХ задач, тож явно передаємо широкий період (рішення користувача).
   *  Задачі з `NULL updated_at` у пошук не потраплять (відоме обмеження). */
  function jrIssueSearch(q: string): Promise<JRIssue[]> {
    return api
      .jrIssues({ q, limit: 10, updatedFrom: '2000-01-01', updatedTo: '2999-12-31' })
      .then((r) => r.items)
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

  /** Явний витяг задач Jira за обраний у попапі період (ніколи не авто, D1).
   *  Тягне ВСІ задачі відстежуваних проектів, **активні** (`updated`) у періоді —
   *  незалежно від worklog-ів і assignee/reporter (`POST /sync/jira/issues-all`).
   *  Після успіху перезавантажує поточну сторінку списку з локальної БД. */
  async function syncJrIssuesAll(period: Period): Promise<void> {
    error.value = null
    try {
      await api.syncJrIssuesAll(period)
      await loadJrIssues()
    } catch (e) {
      error.value = errMsg(e)
      throw e // щоб попап синку показав помилку
    }
  }

  return {
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
    jrPeriod,
    jrStatus,
    jrProjectFilter,
    jrQuery,
    jrOffset,
    jrTotal,
    jrLoading,
    jrStatusOptions,
    jrPageSize: JR_PAGE_SIZE,
    tempoPageSize: TEMPO_PAGE_SIZE,
    // вкладка «Tempo»
    jrWorklogs,
    tempoPeriod,
    tempoLinkFilter,
    tempoQuery,
    tempoOffset,
    tempoTotal,
    tempoLoading,
    loadJrWorklogs,
    setTempoPeriod,
    setTempoLinkFilter,
    setTempoQuery,
    setTempoOffset,
    syncJrWorklogs,
    // вкладка «Конвеєр»
    wst,
    wstSummary,
    wstPeriod,
    wstSyncFilter,
    wstQuery,
    wstOffset,
    wstTotal,
    wstLoading,
    loadWst,
    setWstPeriod,
    setWstSyncFilter,
    setWstQuery,
    setWstOffset,
    pushOneWst,
    error,
    loadTcProjects,
    loadJrProjects,
    loadTcEntries,
    setTcPeriod,
    setTcSyncFilter,
    setTcOffset,
    syncTcEntries,
    loadJrIssues,
    setJrPeriod,
    setJrStatus,
    setJrProjectFilter,
    setJrQuery,
    setJrOffset,
    syncJrIssuesAll,
    saveTcSync,
    jrIssueSearch,
    saveJrWatched,
    syncProjects,
  }
})
