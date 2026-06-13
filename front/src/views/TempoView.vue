<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import DataPage from '@/components/data/DataPage.vue'
import DataTable from '@/components/data/DataTable.vue'
import StatusBadge from '@/components/data/StatusBadge.vue'
import SyncBtn from '@/components/data/SyncBtn.vue'
import type { Column } from '@/components/data/types'
import Btn from '@/components/ui/Btn.vue'
import { type WorklogStatus } from '@/api/types'
import { useI18n } from '@/i18n'
import { secToHm } from '@/lib/format'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()

const sel = ref<Set<string | number>>(new Set())
const pushing = ref(false)

// Реальні стани worklog-sync-task (StatusTaskEnum); 'failed' тут не буває.
const SUMMARY_STATES: WorklogStatus[] = ['pre_create', 'create', 'created']
function summaryCount(s: WorklogStatus): number {
  return store.wstSummary?.[s] ?? 0
}

const cols = computed<Column[]>(() => [
  { key: 'issue_key', label: t.value.col_issue, width: 110 },
  { key: 'content', label: t.value.col_desc },
  { key: 'worker_key', label: t.value.col_worker, width: 120, mono: true },
  { key: 'started_at', label: t.value.col_date, width: 120, mono: true },
  { key: 'time_spent', label: t.value.col_duration, align: 'right', mono: true, width: 90 },
  { key: 'status', label: t.value.col_status, width: 150 },
  { key: 'target_id', label: t.value.col_target, align: 'right', mono: true, width: 110 },
])

async function pushSelected(): Promise<void> {
  if (pushing.value || sel.value.size === 0) return
  pushing.value = true
  try {
    await store.syncWstPush()
    sel.value = new Set()
  } finally {
    pushing.value = false
  }
}

onMounted(() => void store.loadTempo())
</script>

<template>
  <DataPage :title="t.tempo_title" :desc="t.tempo_desc" :error="store.error">
    <template #actions>
      <Btn
        size="sm"
        variant="primary"
        icon="sync"
        :disabled="sel.size === 0 || pushing"
        @click="pushSelected"
      >
        {{ t.tbl_sync_selected }}{{ sel.size > 0 ? ` (${sel.size})` : '' }}
      </Btn>
    </template>

    <template #toolbar>
      <div class="pipe">
        <div class="pipe__summary">
          <div v-for="s in SUMMARY_STATES" :key="s" class="pipe__stat">
            <StatusBadge :status="s" />
            <b class="mono">{{ summaryCount(s) }}</b>
          </div>
        </div>
        <span class="spacer" />
        <div class="pipe__steps">
          <span class="pipe__label mono">pre_create → create → created</span>
          <SyncBtn label="prepare" icon="bolt" :action="() => store.syncWstPrepare()" />
          <SyncBtn label="resolve-issues" icon="bolt" :action="() => store.syncWstResolve()" />
          <SyncBtn label="push-to-tempo" icon="bolt" :action="() => store.syncWstPush()" />
        </div>
      </div>
    </template>

    <DataTable
      v-model:selected="sel"
      :columns="cols"
      :rows="store.wst"
      :get-id="(r) => r.id"
      selectable
      :empty="t.empty"
    >
      <template #cell-issue_key="{ row }">
        <span class="mono key-pill">{{ row.issue_key }}</span>
      </template>
      <template #cell-started_at="{ row }">{{ row.started_at.slice(5, 10) }}</template>
      <template #cell-time_spent="{ row }">{{ secToHm(row.time_spent) }}</template>
      <template #cell-status="{ row }">
        <StatusBadge :status="row.status" />
      </template>
      <template #cell-target_id="{ row }">
        <span v-if="row.target_id">#{{ row.target_id }}</span>
        <span v-else class="faint">—</span>
      </template>
    </DataTable>
  </DataPage>
</template>
