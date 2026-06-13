<script setup lang="ts">
import { computed, onMounted } from 'vue'

import DataPage from '@/components/data/DataPage.vue'
import DataTable from '@/components/data/DataTable.vue'
import ProjTag from '@/components/data/ProjTag.vue'
import type { Column } from '@/components/data/types'
import Badge from '@/components/ui/Badge.vue'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()

// Лише задачі — проекти винесено в окремий екран «Проекти».
const cols = computed<Column[]>(() => [
  { key: 'key', label: t.value.col_key, width: 110 },
  { key: 'name', label: t.value.col_desc },
  { key: 'project', label: t.value.col_project, width: 160 },
  { key: 'status', label: t.value.col_status, width: 140 },
  { key: 'type', label: t.value.col_type, width: 110 },
])

// id → key проекту (для кольорового тегу задачі). jrProjects вантажиться разом
// із задачами в loadIssues().
const projKeyById = computed<Record<number, string>>(() => {
  const map: Record<number, string> = {}
  for (const p of store.jrProjects) map[p.id] = p.key
  return map
})

type Tone = 'neutral' | 'green' | 'amber' | 'accent'
function statusTone(s: string): Tone {
  if (s === 'Done') return 'green'
  if (s === 'To Do') return 'neutral'
  if (s === 'In Review') return 'amber'
  return 'accent'
}

onMounted(async () => {
  await store.loadIssues() // дані з БД одразу
  void store.autoSyncIssues() // у фоні re-sync відомих ключів задач
})
</script>

<template>
  <DataPage :title="t.jr_title" :desc="t.jr_desc" :error="store.error">
    <DataTable
      :columns="cols"
      :rows="store.jrIssues"
      :get-id="(r) => r.id"
      :empty="t.empty"
    >
      <template #cell-key="{ row }">
        <span class="mono key-pill">{{ row.key }}</span>
      </template>
      <template #cell-project="{ row }">
        <ProjTag :label="projKeyById[row.jr_project_id] ?? String(row.jr_project_id)" />
      </template>
      <template #cell-status="{ row }">
        <Badge :tone="statusTone(row.status)" soft dot>{{ row.status }}</Badge>
      </template>
    </DataTable>
  </DataPage>
</template>
