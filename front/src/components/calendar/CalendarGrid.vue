<script setup lang="ts">
import { computed } from 'vue'

import CalendarBlock from '@/components/calendar/CalendarBlock.vue'
import { useI18n } from '@/i18n'
import {
  DAY_START,
  DOW,
  HOUR_H,
  hours,
  type PlacedBlock,
  PXMIN,
  WORK_FROM,
  WORK_TO,
} from '@/lib/calendar'
import { fmtDur } from '@/lib/format'
import { useCalendarStore } from '@/stores/calendar'
import { useUiStore } from '@/stores/ui'

const props = defineProps<{ selectedId: number | null }>()
const emit = defineEmits<{
  (e: 'select', block: PlacedBlock, ev: MouseEvent): void
  (e: 'clear'): void
}>()

const { t } = useI18n()
const store = useCalendarStore()
const ui = useUiStore()

const dark = computed(() => ui.theme === 'dark')
const hoursArr = hours()
const bodyHeight = computed(() => hoursArr.length * HOUR_H)

/** Колонки, що показуються (вихідні ховаються через Tweaks `weekends`). */
const dayIdxs = computed(() => {
  const all = [0, 1, 2, 3, 4, 5, 6]
  return ui.weekends ? all : all.filter((i) => i < 5)
})

const workBandStyle = computed(() => ({
  top: `${(WORK_FROM - DAY_START) * PXMIN}px`,
  height: `${(WORK_TO - WORK_FROM) * PXMIN}px`,
}))

function blkWrapStyle(b: PlacedBlock): Record<string, string> {
  const top = (b.gStart - DAY_START) * PXMIN
  const h = (b.gEnd - b.gStart) * PXMIN
  const w = b.lanes > 1 ? `calc((100% - 6px) / ${b.lanes})` : 'calc(100% - 6px)'
  const left = b.lanes > 1 ? `calc(${b.lane} * (100% - 6px) / ${b.lanes} + 3px)` : '3px'
  return { top: `${top}px`, height: `${h}px`, left, width: w }
}
</script>

<template>
  <div class="cal__scroll">
    <div class="cal__grid" :style="{ gridTemplateColumns: `56px repeat(${dayIdxs.length}, minmax(118px, 1fr))` }">
      <!-- гутер годин -->
      <div class="cal-gutter">
        <div class="cal-gutter__head" />
        <div class="cal-gutter__body">
          <div v-for="h in hoursArr" :key="h" class="cal-gutter__h" :style="{ height: `${HOUR_H}px` }">
            <span class="mono">{{ String(h).padStart(2, '0') }}:00</span>
          </div>
        </div>
      </div>

      <!-- колонки днів -->
      <div
        v-for="di in dayIdxs"
        :key="di"
        :class="['cal-col', { 'is-today': di === store.todayIndex, 'is-weekend': di >= 5 }]"
      >
        <div class="cal-col__head">
          <div class="cal-col__day">
            <span class="cal-col__dow">{{ t[DOW[di]] }}</span>
            <span :class="['cal-col__date', { 'is-today': di === store.todayIndex }]">
              {{ store.weekDates[di] }}
            </span>
          </div>
          <span class="cal-col__total mono">
            {{ store.dayTotals[di] ? fmtDur(store.dayTotals[di]) : '—' }}
          </span>
        </div>

        <div class="cal-col__body" :style="{ height: `${bodyHeight}px` }" @click="emit('clear')">
          <!-- лінії годин -->
          <div v-for="(h, i) in hoursArr" :key="`l${h}`" class="cal-line" :style="{ top: `${i * HOUR_H}px` }" />
          <!-- смуга робочих годин (Tweaks) -->
          <div v-if="ui.workBand" class="cal-work" :style="workBandStyle" />
          <!-- лінія «зараз» лише сьогодні -->
          <div
            v-if="di === store.todayIndex"
            class="cal-now"
            :style="{ top: `${(store.nowMin - DAY_START) * PXMIN}px` }"
          >
            <span />
          </div>
          <!-- блоки -->
          <div v-for="b in store.byDay[di]" :key="b.id" class="cal-blk-wrap" :style="blkWrapStyle(b)">
            <CalendarBlock
              :block="b"
              :variant="store.variant"
              :dark="dark"
              :selected="props.selectedId === b.id"
              @select="(ev) => emit('select', b, ev)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
