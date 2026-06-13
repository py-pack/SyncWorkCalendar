<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import DataTable from '@/components/data/DataTable.vue'
import PageHeader from '@/components/data/PageHeader.vue'
import ProjTag from '@/components/data/ProjTag.vue'
import Tabs from '@/components/data/Tabs.vue'
import type { Column, TabItem } from '@/components/data/types'
import Badge from '@/components/ui/Badge.vue'
import Icon from '@/components/ui/Icon.vue'
import Toggle from '@/components/ui/Toggle.vue'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()

const tab = ref<'projects' | 'issues'>('projects')

const tabs = computed<TabItem[]>(() => [
  { id: 'projects', label: t.value.tab_projects, icon: 'table', count: store.jrProjects.length },
  { id: 'issues', label: t.value.tab_issues, icon: 'inbox', count: store.jrIssues.length },
])

const projCols = computed<Column[]>(() => [
  { key: 'key', label: t.value.col_key, width: 90 },
  { key: 'name', label: t.value.col_name },
  { key: 'issues_count', label: t.value.col_issues, align: 'right', mono: true, width: 90 },
  { key: 'is_watched', label: t.value.col_watched, align: 'right', width: 90 },
])

const issueCols = computed<Column[]>(() => [
  { key: 'key', label: t.value.col_key, width: 110 },
  { key: 'name', label: t.value.col_desc },
  { key: 'project', label: t.value.col_project, width: 160 },
  { key: 'status', label: t.value.col_status, width: 140 },
  { key: 'type', label: t.value.col_type, width: 110 },
])

// id → key проекту (для кольорового тегу задачі)
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
  await store.loadJira() // дані з БД одразу
  void store.autoSyncJira() // у фоні освіжаємо з Jira
})
</script>

<template>
  <div class="page">
    <PageHeader :title="t.jr_title" :desc="t.jr_desc" />

    <Tabs v-model="tab" :tabs="tabs" />

    <p v-if="store.error" class="data-error"><Icon name="alert" :size="15" />{{ store.error }}</p>

    <div class="page__body">
      <DataTable
        v-if="tab === 'projects'"
        :columns="projCols"
        :rows="store.jrProjects"
        :get-id="(r) => r.id"
        :empty="t.empty"
      >
        <template #cell-key="{ row }">
          <span class="mono key-pill">{{ row.key }}</span>
        </template>
        <template #cell-name="{ row }">
          <div class="dt-name">
            {{ row.name }}
            <Badge v-if="row.is_archived" tone="neutral" soft>{{ t.col_archived }}</Badge>
          </div>
        </template>
        <template #cell-is_watched="{ row }">
          <Toggle size="sm" :checked="row.is_watched" @update:checked="store.toggleJrWatched(row)" />
        </template>
      </DataTable>

      <DataTable
        v-else
        :columns="issueCols"
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
    </div>
  </div>
</template>
