<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import type { Period, TCSyncFilter } from '@/api/types'
import DataPage from '@/components/data/DataPage.vue'
import DataTable from '@/components/data/DataTable.vue'
import PeriodPicker from '@/components/data/PeriodPicker.vue'
import SyncFilter from '@/components/data/SyncFilter.vue'
import SyncState from '@/components/data/SyncState.vue'
import type { Column } from '@/components/data/types'
import SyncEntriesModal from '@/components/timecamp/SyncEntriesModal.vue'
import Btn from '@/components/ui/Btn.vue'
import { useI18n } from '@/i18n'
import { durationMin, fmtDate, fmtDur } from '@/lib/format'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()

// Усі записи з локальної БД за період (без вкладок) — проекти на екрані «Проекти».
// Порядок колонок: Проект → Задача → Опис → Дата → Час → Стан синку.
const cols = computed<Column[]>(() => [
  { key: 'tc_project_name', label: t.value.col_project },
  { key: 'issue_key', label: t.value.col_issue, width: 110 },
  { key: 'description', label: t.value.col_desc },
  { key: 'start_at', label: t.value.col_date, mono: true, width: 110 },
  { key: 'dur', label: t.value.col_duration, align: 'right', mono: true, width: 80 },
  { key: 'synced', label: t.value.col_status, width: 120 },
])

function onFilter(v: TCSyncFilter): void {
  void store.setTcSyncFilter(v)
}
function onPeriod(p: Period): void {
  void store.setTcPeriod(p)
}

// --- пагінація ------------------------------------------------------------
const canPrev = computed(() => store.tcOffset > 0)
const canNext = computed(() => store.tcOffset + store.tcPageSize < store.tcTotal)
const pageInfo = computed(() => {
  const from = store.tcTotal === 0 ? 0 : store.tcOffset + 1
  const to = Math.min(store.tcOffset + store.tcPageSize, store.tcTotal)
  return `${from}–${to} / ${store.tcTotal}`
})
function prev(): void {
  void store.setTcOffset(store.tcOffset - store.tcPageSize)
}
function next(): void {
  void store.setTcOffset(store.tcOffset + store.tcPageSize)
}

// --- попап синку ----------------------------------------------------------
const syncOpen = ref(false)

// Лише читання з БД при відкритті — жодного авто-синку (D1).
onMounted(() => void store.loadTcEntries())
</script>

<template>
  <DataPage :title="t.tc_title" :desc="t.tc_desc" :error="store.error">
    <template #actions>
      <Btn variant="default" size="sm" icon="sync" @click="syncOpen = true">{{ t.tc_sync }}</Btn>
    </template>

    <template #toolbar>
      <div class="pipe tcbar">
        <PeriodPicker :model-value="store.tcPeriod" @update:model-value="onPeriod" />
        <SyncFilter :model-value="store.tcSyncFilter" @update:model-value="onFilter" />
      </div>
    </template>

    <DataTable
      :columns="cols"
      :rows="store.tcEntries"
      :get-id="(r) => r.id"
      :empty="t.empty"
    >
      <template #cell-issue_key="{ row }">
        <span v-if="row.issue_key" class="key-pill mono">{{ row.issue_key }}</span>
        <span v-else class="faint">—</span>
      </template>
      <template #cell-description="{ row }">
        <span class="mono">{{ row.description }}</span>
      </template>
      <template #cell-start_at="{ row }">{{ fmtDate(row.start_at) }}</template>
      <template #cell-dur="{ row }">{{ fmtDur(durationMin(row.start_at, row.end_at)) }}</template>
      <template #cell-synced="{ row }">
        <SyncState :synced="row.is_synced" />
      </template>
    </DataTable>

    <div v-if="store.tcTotal > store.tcPageSize" class="tcpage">
      <Btn size="sm" variant="ghost" icon="chevL" :disabled="!canPrev" @click="prev">
        {{ t.page_prev }}
      </Btn>
      <span class="tcpage__pos mono">{{ pageInfo }}</span>
      <Btn size="sm" variant="ghost" icon-right="chevR" :disabled="!canNext" @click="next">
        {{ t.page_next }}
      </Btn>
    </div>

    <SyncEntriesModal :open="syncOpen" @close="syncOpen = false" />
  </DataPage>
</template>
