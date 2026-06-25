<script setup lang="ts">
// Вкладка «Tempo» (rework-tempo-screen): реальні Tempo-worklog-и з локальної БД
// (GET /jr-worklogs) за період/фільтр/пошук + серверна пагінація. Стан синку =
// звʼязаний із нашим WST (is_linked) — спільні SyncState/SyncFilter («мова синку»).
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import type { Period, SyncTri } from '@/api/types'
import DataTable from '@/components/data/DataTable.vue'
import PeriodPicker from '@/components/data/PeriodPicker.vue'
import SyncFilter from '@/components/data/SyncFilter.vue'
import SyncState from '@/components/data/SyncState.vue'
import type { Column } from '@/components/data/types'
import Btn from '@/components/ui/Btn.vue'
import { useI18n } from '@/i18n'
import { fmtDate, secToHm } from '@/lib/format'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()

// Кожен рядок показує номер (key) і назву задачі (issue_name).
const cols = computed<Column[]>(() => [
  { key: 'issue', label: t.value.col_issue, width: 280 },
  { key: 'description', label: t.value.col_desc },
  { key: 'started_at', label: t.value.col_date, mono: true, width: 110 },
  { key: 'duration', label: t.value.col_duration, align: 'right', mono: true, width: 90 },
  { key: 'linked', label: t.value.col_status, width: 120 },
])

function onPeriod(p: Period): void {
  void store.setTempoPeriod(p)
}
function onFilter(v: SyncTri): void {
  void store.setTempoLinkFilter(v)
}

// Пошук за назвою задачі — з debounce.
const queryInput = ref(store.tempoQuery)
let timer: ReturnType<typeof setTimeout> | undefined
watch(queryInput, (q) => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => void store.setTempoQuery(q.trim()), 300)
})
onBeforeUnmount(() => {
  if (timer) clearTimeout(timer)
})

// --- пагінація ---
const canPrev = computed(() => store.tempoOffset > 0)
const canNext = computed(() => store.tempoOffset + store.tempoPageSize < store.tempoTotal)
const pageInfo = computed(() => {
  const from = store.tempoTotal === 0 ? 0 : store.tempoOffset + 1
  const to = Math.min(store.tempoOffset + store.tempoPageSize, store.tempoTotal)
  return `${from}–${to} / ${store.tempoTotal}`
})
function prev(): void {
  void store.setTempoOffset(store.tempoOffset - store.tempoPageSize)
}
function next(): void {
  void store.setTempoOffset(store.tempoOffset + store.tempoPageSize)
}

// Лише читання з БД при відкритті — синк окремою дією «Забрати з Tempo» (D1).
onMounted(() => void store.loadJrWorklogs())
</script>

<template>
  <div class="tempotab">
    <div class="pipe tcbar">
      <PeriodPicker :model-value="store.tempoPeriod" @update:model-value="onPeriod" />
      <SyncFilter :model-value="store.tempoLinkFilter" @update:model-value="onFilter" />
      <input v-model="queryInput" class="sw-input jrbar__search" :placeholder="t.tmp_search" />
    </div>

    <DataTable :columns="cols" :rows="store.jrWorklogs" :get-id="(r) => r.id" :empty="t.empty">
      <template #cell-issue="{ row }">
        <div class="tmpissue">
          <span v-if="row.issue_key" class="mono key-pill">{{ row.issue_key }}</span>
          <span v-else class="faint">—</span>
          <span v-if="row.issue_name" class="tmpissue__name">{{ row.issue_name }}</span>
        </div>
      </template>
      <template #cell-description="{ row }">
        <span class="mono">{{ row.description }}</span>
      </template>
      <template #cell-started_at="{ row }">{{ fmtDate(row.started_at) }}</template>
      <template #cell-duration="{ row }">{{ secToHm(row.duration) }}</template>
      <template #cell-linked="{ row }">
        <SyncState :synced="row.is_linked" />
      </template>
    </DataTable>

    <div v-if="store.tempoTotal > store.tempoPageSize" class="tcpage">
      <Btn size="sm" variant="ghost" icon="chevL" :disabled="!canPrev" @click="prev">
        {{ t.page_prev }}
      </Btn>
      <span class="tcpage__pos mono">{{ pageInfo }}</span>
      <Btn size="sm" variant="ghost" icon-right="chevR" :disabled="!canNext" @click="next">
        {{ t.page_next }}
      </Btn>
    </div>
  </div>
</template>
