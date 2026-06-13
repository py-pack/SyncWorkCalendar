<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import BlockPopover from '@/components/calendar/BlockPopover.vue'
import CalendarFilters from '@/components/calendar/CalendarFilters.vue'
import CalendarGrid from '@/components/calendar/CalendarGrid.vue'
import CalendarToolbar from '@/components/calendar/CalendarToolbar.vue'
import Icon from '@/components/ui/Icon.vue'
import { useI18n } from '@/i18n'
import type { CalendarBlock } from '@/api/types'
import type { PlacedBlock } from '@/lib/calendar'
import { useCalendarStore } from '@/stores/calendar'
import { useUiStore } from '@/stores/ui'

const { t } = useI18n()
const store = useCalendarStore()
const ui = useUiStore()

const showFilters = ref(true)
const pop = ref<{ block: CalendarBlock; anchor: { x: number; y: number } } | null>(null)
const dark = computed(() => ui.theme === 'dark')
const isEmpty = computed(() => !store.loading && !store.error && store.blocks.length === 0)

function onSelect(placed: PlacedBlock, ev: MouseEvent): void {
  const raw = store.blocks.find((b) => b.id === placed.id)
  if (raw) pop.value = { block: raw, anchor: { x: ev.clientX, y: ev.clientY } }
}
function closePop(): void {
  pop.value = null
}

onMounted(() => void store.load())
</script>

<template>
  <div class="cal">
    <CalendarToolbar v-model:show-filters="showFilters" />
    <CalendarFilters v-if="showFilters" />

    <p v-if="store.error" class="data-error"><Icon name="alert" />{{ store.error }}</p>

    <div v-if="isEmpty" class="cal__empty">
      <Icon name="calendar" :size="34" :stroke="1.3" />
      <p>{{ t.cal_empty }}</p>
    </div>
    <CalendarGrid v-else :selected-id="pop?.block.id ?? null" @select="onSelect" @clear="closePop" />

    <BlockPopover v-if="pop" :block="pop.block" :anchor="pop.anchor" :dark="dark" @close="closePop" />
  </div>
</template>
