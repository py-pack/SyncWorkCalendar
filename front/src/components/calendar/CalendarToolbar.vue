<script setup lang="ts">
import { computed } from 'vue'

import Btn from '@/components/ui/Btn.vue'
import IconBtn from '@/components/ui/IconBtn.vue'
import Segmented from '@/components/ui/Segmented.vue'
import { useI18n } from '@/i18n'
import { fmtDur } from '@/lib/format'
import { useCalendarStore } from '@/stores/calendar'

const props = defineProps<{ showFilters: boolean }>()
const emit = defineEmits<{ (e: 'update:showFilters', value: boolean): void }>()

const { t, lang } = useI18n()
const store = useCalendarStore()

const locale = computed(() => (lang.value === 'uk' ? 'uk-UA' : 'en-US'))

/** «1 – 7 червня» / «29 червня – 5 липня». */
const rangeMain = computed(() => {
  const s = store.weekStart
  const e = store.weekEnd
  const dm = (d: Date) => new Intl.DateTimeFormat(locale.value, { day: 'numeric', month: 'long' }).format(d)
  if (s.getMonth() === e.getMonth()) return `${s.getDate()} – ${dm(e)}`
  return `${dm(s)} – ${dm(e)}`
})
const rangeSub = computed(() => `${store.weekStart.getFullYear()} · W${store.weekNo}`)

const variantOptions = computed(() => [
  { value: 'basic', label: t.value.cal_variant_basic },
  { value: 'soft', label: t.value.cal_variant_soft },
  { value: 'bold', label: t.value.cal_variant_bold },
])
</script>

<template>
  <div class="cal__toolbar">
    <div class="cal__nav">
      <IconBtn name="chevL" variant="outline" size="sm" :title="t.week" @click="store.shift(-1)" />
      <Btn size="sm" variant="default" @click="store.goToday()">{{ t.today }}</Btn>
      <IconBtn name="chevR" variant="outline" size="sm" :title="t.week" @click="store.shift(1)" />
    </div>

    <div class="cal__range">
      <span class="cal__range-main">{{ rangeMain }}</span>
      <span class="cal__range-sub mono">{{ rangeSub }}</span>
    </div>

    <span class="spacer" />

    <div class="cal__totals">
      <div class="cal__total">
        <span class="muted">{{ t.cal_total }}</span>
        <b class="mono">{{ fmtDur(store.weekTotal) }}</b>
      </div>
      <div class="cal__total">
        <span class="muted">{{ t.cal_billable }}</span>
        <b class="mono">{{ fmtDur(store.billableTotal) }}</b>
      </div>
    </div>

    <div class="cal__tbsep" />

    <Segmented
      :model-value="store.variant"
      size="sm"
      :options="variantOptions"
      @update:model-value="(v) => store.setVariant(v as 'basic' | 'soft' | 'bold')"
    />
    <IconBtn
      name="filter"
      variant="outline"
      size="sm"
      :active="props.showFilters"
      :title="t.cal_filters"
      @click="emit('update:showFilters', !props.showFilters)"
    />
  </div>
</template>
