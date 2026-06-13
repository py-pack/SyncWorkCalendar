<script setup lang="ts">
// Під-вʼюха «Проекти → Jira». Дані вантажить батьківський ProjectsView;
// тут лише розмітка таблиці й тогл is_watched (перенесено з JiraView).
import { computed } from 'vue'

import DataTable from '@/components/data/DataTable.vue'
import type { Column } from '@/components/data/types'
import Badge from '@/components/ui/Badge.vue'
import Toggle from '@/components/ui/Toggle.vue'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()

const cols = computed<Column[]>(() => [
  { key: 'key', label: t.value.col_key, width: 90 },
  { key: 'name', label: t.value.col_name },
  { key: 'issues_count', label: t.value.col_issues, align: 'right', mono: true, width: 90 },
  { key: 'is_watched', label: t.value.col_watched, align: 'right', width: 90 },
])
</script>

<template>
  <DataTable :columns="cols" :rows="store.jrProjects" :get-id="(r) => r.id" :empty="t.empty">
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
</template>
