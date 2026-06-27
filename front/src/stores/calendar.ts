/* =========================================================================
   Sync Work — read-only store тижневого календаря (фаза 2, D4).
   Тримає блоки тижня, обраний тиждень, фільтри (проект/статус) і варіант
   вигляду. Жодних мутацій блоків — лише читання GET /calendar і навігація.
   ========================================================================= */
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { api } from '@/api/client'
import { ApiError, type CalendarBlock, type CalendarStatus } from '@/api/types'
import {
  addDays,
  CAL_STATES,
  hueForProject,
  isoDate,
  layoutWeek,
  mondayOf,
  projectId,
  weekNumber,
} from '@/lib/calendar'
import { useStored } from '@/lib/storage'

export type BlockVariant = 'basic' | 'soft' | 'bold'

/** Чип проекту у фільтрі. */
export interface CalProjectChip {
  id: string
  name: string
  hue: number
  on: boolean
}

export const useCalendarStore = defineStore('calendar', () => {
  const blocks = ref<CalendarBlock[]>([])
  const anchor = ref<Date>(new Date()) // будь-яка дата в обраному тижні
  const variant = useStored<BlockVariant>('cal.variant', 'soft')
  const hiddenProj = ref<Set<string>>(new Set())
  const hiddenStatus = ref<Set<CalendarStatus>>(new Set())
  const onlyDups = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // --- тиждень ---------------------------------------------------------------
  const weekStart = computed(() => mondayOf(anchor.value))
  const weekEnd = computed(() => addDays(weekStart.value, 6))
  const weekStartIso = computed(() => isoDate(weekStart.value))
  const weekNo = computed(() => weekNumber(weekStart.value))
  /** Числа місяця Пн..Нд для шапок колонок. */
  const weekDates = computed(() =>
    Array.from({ length: 7 }, (_, i) => String(addDays(weekStart.value, i).getDate())),
  )

  const todayIndex = computed(() => {
    const today = isoDate(new Date())
    const diff = Math.round(
      (new Date(today).getTime() - new Date(weekStartIso.value).getTime()) / 86400000,
    )
    return diff >= 0 && diff <= 6 ? diff : -1
  })
  const nowMin = computed(() => {
    const n = new Date()
    return n.getHours() * 60 + n.getMinutes()
  })

  // --- фільтри ---------------------------------------------------------------
  const visible = computed(() =>
    blocks.value.filter(
      (b) =>
        !hiddenProj.value.has(projectId(b.project)) &&
        !hiddenStatus.value.has(b.status) &&
        (!onlyDups.value || b.duplicate),
    ),
  )

  /** Чи є взагалі дублі цього тижня (для показу/підсвітки чипа фільтра). */
  const hasDups = computed(() => blocks.value.some((b) => b.duplicate))

  /** Усі проекти (з усіх блоків, не лише видимих) для чипів фільтра. */
  const projects = computed<CalProjectChip[]>(() => {
    const map = new Map<string, CalProjectChip>()
    for (const b of blocks.value) {
      const id = projectId(b.project)
      if (!map.has(id)) {
        map.set(id, { id, name: b.project.name || id, hue: hueForProject(b.project), on: !hiddenProj.value.has(id) })
      }
    }
    return [...map.values()].sort((a, b) => a.name.localeCompare(b.name))
  })

  /** Чипи статусів (легенда фільтра). */
  const statuses = computed(() =>
    CAL_STATES.map((s) => ({ status: s, on: !hiddenStatus.value.has(s) })),
  )

  // --- розкладка/тоталі ------------------------------------------------------
  const layout = computed(() => layoutWeek(visible.value, weekStartIso.value))
  const byDay = computed(() => layout.value.byDay)
  const dayTotals = computed(() => layout.value.dayTotals)
  const weekTotal = computed(() => dayTotals.value.reduce((a, b) => a + b, 0))
  // Білабл-тотал — заглушка: `billable` ще не персиститься (D3), тож = тижневому.
  const billableTotal = computed(() => weekTotal.value)

  // --- дії -------------------------------------------------------------------
  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const res = await api.calendar({ start: weekStartIso.value, end: isoDate(weekEnd.value) })
      blocks.value = res.blocks
    } catch (e) {
      error.value = e instanceof ApiError ? e.detail : String(e)
      blocks.value = []
    } finally {
      loading.value = false
    }
  }

  function shift(weeks: number): void {
    anchor.value = addDays(weekStart.value, weeks * 7)
    void load()
  }
  function goToday(): void {
    anchor.value = new Date()
    void load()
  }
  function toggleProj(id: string): void {
    const n = new Set(hiddenProj.value)
    n.has(id) ? n.delete(id) : n.add(id)
    hiddenProj.value = n
  }
  function toggleStatus(s: CalendarStatus): void {
    const n = new Set(hiddenStatus.value)
    n.has(s) ? n.delete(s) : n.add(s)
    hiddenStatus.value = n
  }
  function toggleOnlyDups(): void {
    onlyDups.value = !onlyDups.value
  }
  function setVariant(v: BlockVariant): void {
    variant.value = v
  }

  return {
    blocks, variant, loading, error, onlyDups,
    weekStart, weekEnd, weekNo, weekDates, todayIndex, nowMin,
    visible, projects, statuses, hasDups,
    byDay, dayTotals, weekTotal, billableTotal,
    load, shift, goToday, toggleProj, toggleStatus, toggleOnlyDups, setVariant,
  }
})
