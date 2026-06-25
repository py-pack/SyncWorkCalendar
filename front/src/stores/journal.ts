/* =========================================================================
   Sync Work — стор журналу синку (api_jobs). Читає ЛИШЕ з локальної БД через
   GET /api-jobs: фільтр за періодом (`started_at`), статусом і тригером +
   серверна пагінація (`limit`/`offset`/`total`). Деталі job-а
   (payload/result/error) і крок verify; рядки оновлюються локально без повного
   перезавантаження. needsVerification живить лічильник у навігації.

   «Мова синку» (SyncState/SyncFilter) тут НЕ застосовується — статус job-а це
   4-станова машина життєвого циклу, а не бінарне synced/not-synced.
   ========================================================================= */
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api } from '@/api/client'
import {
  ApiError,
  type ApiJobDetail,
  type ApiJobStatus,
  type ApiJobStatusSummary,
  type ApiJobSummary,
  type Period,
} from '@/api/types'
import { defaultReviewPeriod } from '@/lib/period'

const PAGE_SIZE = 50

function emptySummary(): ApiJobStatusSummary {
  return { running: 0, needs_verification: 0, verified: 0, failed: 0 }
}

function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.detail
  return e instanceof Error ? e.message : String(e)
}

export const useJournalStore = defineStore('journal', () => {
  const jobs = ref<ApiJobSummary[]>([])
  const total = ref(0)
  // Зведення лічильників по статусах за період+тригер (ігнорує фільтр статусу).
  const summary = ref<ApiJobStatusSummary>(emptySummary())
  // Дефолт — поточний місяць (журнал — свіжа активність, job-и щодня).
  const period = ref<Period>(defaultReviewPeriod())
  const statusFilter = ref<ApiJobStatus | null>(null)
  const triggerFilter = ref<string | null>(null)
  const offset = ref(0)
  const detail = ref<ApiJobDetail | null>(null)
  const error = ref<string | null>(null)
  // Лічильник для бейджа навігації — незалежний від поточного фільтра списку.
  const needsCount = ref(0)

  async function refreshNeedsCount(): Promise<void> {
    try {
      const res = await api.apiJobs({ status: 'needs_verification', limit: 1 })
      needsCount.value = res.total
    } catch {
      /* бейдж — не критично; тиха невдача */
    }
  }

  async function load(): Promise<void> {
    error.value = null
    try {
      const res = await api.apiJobs({
        status: statusFilter.value ?? undefined,
        trigger_name: triggerFilter.value ?? undefined,
        start: period.value.start,
        end: period.value.end,
        limit: PAGE_SIZE,
        offset: offset.value,
      })
      jobs.value = res.items
      total.value = res.total
      summary.value = res.summary
    } catch (e) {
      error.value = errMsg(e)
    }
    void refreshNeedsCount()
  }

  // Зміна періоду чи будь-якого фільтра скидає пагінацію у 0 і перезавантажує.
  function setPeriod(p: Period): Promise<void> {
    period.value = p
    offset.value = 0
    return load()
  }

  function setStatusFilter(s: ApiJobStatus | null): Promise<void> {
    statusFilter.value = s
    offset.value = 0
    return load()
  }

  function setTriggerFilter(tr: string | null): Promise<void> {
    triggerFilter.value = tr
    offset.value = 0
    return load()
  }

  function setOffset(o: number): Promise<void> {
    const max = Math.max(0, total.value - 1)
    offset.value = Math.min(Math.max(0, o), max)
    return load()
  }

  async function open(id: string): Promise<void> {
    detail.value = null
    try {
      detail.value = await api.apiJob(id)
    } catch (e) {
      error.value = errMsg(e)
    }
  }

  function close(): void {
    detail.value = null
  }

  async function verify(id: string): Promise<void> {
    const updated = await api.verifyJob(id)
    jobs.value = jobs.value.map((j) =>
      j.id === id
        ? {
            ...j,
            status: updated.status,
            verified_by: updated.verified_by,
            verified_at: updated.verified_at,
            finished_at: updated.finished_at,
          }
        : j,
    )
    if (detail.value?.id === id) detail.value = updated
    needsCount.value = Math.max(0, needsCount.value - 1)
  }

  // Масово підтвердити всі `needs_verification` за поточними фільтрами (період +
  // тригер; `status` завжди needs_verification). Після успіху — релоад списку,
  // зведення й навбейджа (їх оновлює `load`).
  async function verifyAll(): Promise<void> {
    error.value = null
    try {
      await api.verifyAllJobs({
        start: period.value.start,
        end: period.value.end,
        trigger_name: triggerFilter.value ?? undefined,
      })
    } catch (e) {
      error.value = errMsg(e)
      return
    }
    await load()
  }

  return {
    jobs,
    total,
    summary,
    period,
    statusFilter,
    triggerFilter,
    offset,
    pageSize: PAGE_SIZE,
    detail,
    error,
    needsCount,
    load,
    refreshNeedsCount,
    setPeriod,
    setStatusFilter,
    setTriggerFilter,
    setOffset,
    open,
    close,
    verify,
    verifyAll,
  }
})
