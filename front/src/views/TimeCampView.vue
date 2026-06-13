<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import DataTable from '@/components/data/DataTable.vue'
import PageHeader from '@/components/data/PageHeader.vue'
import Tabs from '@/components/data/Tabs.vue'
import type { Column, TabItem } from '@/components/data/types'
import Badge from '@/components/ui/Badge.vue'
import Btn from '@/components/ui/Btn.vue'
import Icon from '@/components/ui/Icon.vue'
import Toggle from '@/components/ui/Toggle.vue'
import { useI18n } from '@/i18n'
import { durationMin, fmtDur } from '@/lib/format'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()

const tab = ref<'projects' | 'untracked'>('projects')

const tabs = computed<TabItem[]>(() => [
  { id: 'projects', label: t.value.tab_projects, icon: 'table', count: store.tcProjects.length },
  { id: 'untracked', label: t.value.tab_untracked, icon: 'alert', count: store.tcUntracked.length },
])

const projCols = computed<Column[]>(() => [
  { key: 'name', label: t.value.col_name },
  { key: 'issue_key', label: t.value.col_mapping },
  { key: 'entries_count', label: t.value.col_entries, align: 'right', mono: true, width: 90 },
  { key: 'is_sync', label: t.value.col_sync_on, align: 'right', width: 90 },
])

const untrCols = computed<Column[]>(() => [
  { key: 'description', label: t.value.col_desc },
  { key: 'tc_project_name', label: t.value.col_project },
  { key: 'start_at', label: t.value.col_date, mono: true, width: 130 },
  { key: 'dur', label: t.value.col_duration, align: 'right', mono: true, width: 90 },
  { key: 'act', label: '', align: 'right', width: 120 },
])

onMounted(async () => {
  await store.loadTimeCamp() // дані з БД одразу
  void store.autoSyncTimeCamp() // у фоні освіжаємо з TimeCamp
})
</script>

<template>
  <div class="page">
    <PageHeader :title="t.tc_title" :desc="t.tc_desc" />

    <Tabs v-model="tab" :tabs="tabs" />

    <p v-if="store.error" class="data-error"><Icon name="alert" :size="15" />{{ store.error }}</p>

    <div class="page__body">
      <DataTable
        v-if="tab === 'projects'"
        :columns="projCols"
        :rows="store.tcProjects"
        :get-id="(r) => r.id"
        :empty="t.empty"
      >
        <template #cell-name="{ row }">
          <div class="dt-name">
            <span class="mono dt-name__id">#{{ row.id }}</span>
            {{ row.name }}
            <Badge v-if="row.is_archived" tone="neutral" soft>{{ t.col_archived }}</Badge>
          </div>
        </template>
        <template #cell-issue_key="{ row }">
          <span v-if="row.issue_key" class="map-arrow">
            <span class="mono">{{ row.issue_key }}</span>
            <Icon name="arrowRight" :size="13" />
          </span>
          <span v-else class="faint">—</span>
        </template>
        <template #cell-is_sync="{ row }">
          <Toggle size="sm" :checked="row.is_sync" @update:checked="store.toggleTcSync(row)" />
        </template>
      </DataTable>

      <DataTable
        v-else
        :columns="untrCols"
        :rows="store.tcUntracked"
        :get-id="(r) => r.id"
        :empty="t.empty"
      >
        <template #cell-description="{ row }">
          <span class="mono">{{ row.description }}</span>
        </template>
        <template #cell-start_at="{ row }">{{ row.start_at.slice(5, 10) }}</template>
        <template #cell-dur="{ row }">{{ fmtDur(durationMin(row.start_at, row.end_at)) }}</template>
        <template #cell-act>
          <Btn size="sm" variant="ghost" icon="link" disabled>{{ t.tc_match }}</Btn>
        </template>
      </DataTable>
    </div>
  </div>
</template>
