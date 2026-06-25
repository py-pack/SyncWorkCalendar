<script setup lang="ts">
// Вкладка «Конвеєр синку» (rework-tempo-screen, D4): worklog_sync_tasks
// (GET /worklog-sync-tasks) за період/фільтр/пошук + пагінація. Стан синку =
// запушено в Tempo (target_id). Замість чекбоксів і «Синхронізувати обрані» —
// пер-рядкова кнопка дії (один пуш через POST /sync/worklog-tasks/{id}/push).
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import type { Period, SyncTri } from '@/api/types'
import DataTable from '@/components/data/DataTable.vue'
import PeriodPicker from '@/components/data/PeriodPicker.vue'
import SyncBtn from '@/components/data/SyncBtn.vue'
import SyncFilter from '@/components/data/SyncFilter.vue'
import SyncState from '@/components/data/SyncState.vue'
import type { Column } from '@/components/data/types'
import Btn from '@/components/ui/Btn.vue'
import { useI18n } from '@/i18n'
import { fmtDate, secToHm } from '@/lib/format'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()

const cols = computed<Column[]>(() => [
  { key: 'issue', label: t.value.col_issue, width: 280 },
  { key: 'content', label: t.value.col_desc },
  { key: 'started_at', label: t.value.col_date, mono: true, width: 110 },
  { key: 'time_spent', label: t.value.col_duration, align: 'right', mono: true, width: 90 },
  { key: 'synced', label: t.value.col_status, width: 120 },
  { key: 'act', label: '', align: 'right', width: 150 },
])

function onPeriod(p: Period): void {
  void store.setWstPeriod(p)
}
function onFilter(v: SyncTri): void {
  void store.setWstSyncFilter(v)
}

const queryInput = ref(store.wstQuery)
let timer: ReturnType<typeof setTimeout> | undefined
watch(queryInput, (q) => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => void store.setWstQuery(q.trim()), 300)
})
onBeforeUnmount(() => {
  if (timer) clearTimeout(timer)
})

// --- пагінація ---
const canPrev = computed(() => store.wstOffset > 0)
const canNext = computed(() => store.wstOffset + store.tempoPageSize < store.wstTotal)
const pageInfo = computed(() => {
  const from = store.wstTotal === 0 ? 0 : store.wstOffset + 1
  const to = Math.min(store.wstOffset + store.tempoPageSize, store.wstTotal)
  return `${from}–${to} / ${store.wstTotal}`
})
function prev(): void {
  void store.setWstOffset(store.wstOffset - store.tempoPageSize)
}
function next(): void {
  void store.setWstOffset(store.wstOffset + store.tempoPageSize)
}

onMounted(() => void store.loadWst())
</script>

<template>
  <div class="tempotab">
    <div class="pipe tcbar">
      <PeriodPicker :model-value="store.wstPeriod" @update:model-value="onPeriod" />
      <SyncFilter :model-value="store.wstSyncFilter" @update:model-value="onFilter" />
      <input v-model="queryInput" class="sw-input jrbar__search" :placeholder="t.tmp_search" />
    </div>

    <DataTable :columns="cols" :rows="store.wst" :get-id="(r) => r.id" :empty="t.empty">
      <template #cell-issue="{ row }">
        <div class="tmpissue">
          <span class="mono key-pill">{{ row.issue_key }}</span>
          <span v-if="row.issue_name" class="tmpissue__name">{{ row.issue_name }}</span>
        </div>
      </template>
      <template #cell-content="{ row }">
        <span class="mono">{{ row.content }}</span>
      </template>
      <template #cell-started_at="{ row }">{{ fmtDate(row.started_at) }}</template>
      <template #cell-time_spent="{ row }">{{ secToHm(row.time_spent) }}</template>
      <template #cell-synced="{ row }">
        <SyncState :synced="!!row.target_id" />
      </template>
      <template #cell-act="{ row }">
        <SyncBtn
          v-if="!row.target_id"
          size="sm"
          :label="t.tmp_push_row"
          icon="sync"
          :action="() => store.pushOneWst(row.id)"
        />
        <span v-else class="faint">—</span>
      </template>
    </DataTable>

    <div v-if="store.wstTotal > store.tempoPageSize" class="tcpage">
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
