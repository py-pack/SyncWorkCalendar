/* =========================================================================
   Sync Work — стор журналу синку (api_jobs). Фільтр за статусом, деталі job-а
   (payload/result/error) і крок verify; рядки оновлюються локально без повного
   перезавантаження. needsVerification живить лічильник у навігації.
   ========================================================================= */
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api } from '@/api/client'
import {
  ApiError,
  type ApiJobDetail,
  type ApiJobStatus,
  type ApiJobSummary,
} from '@/api/types'

export type JournalFilter = 'all' | ApiJobStatus

function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.detail
  return e instanceof Error ? e.message : String(e)
}

export const useJournalStore = defineStore('journal', () => {
  const jobs = ref<ApiJobSummary[]>([])
  const total = ref(0)
  const filter = ref<JournalFilter>('all')
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
      const res = await api.apiJobs(
        filter.value === 'all' ? {} : { status: filter.value },
      )
      jobs.value = res.items
      total.value = res.total
    } catch (e) {
      error.value = errMsg(e)
    }
    void refreshNeedsCount()
  }

  function setFilter(f: JournalFilter): void {
    filter.value = f
    void load()
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

  return {
    jobs,
    total,
    filter,
    detail,
    error,
    needsCount,
    load,
    refreshNeedsCount,
    setFilter,
    open,
    close,
    verify,
  }
})
