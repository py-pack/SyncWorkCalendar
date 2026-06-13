<script setup lang="ts">
// Під-вʼюха «Проекти → TimeCamp». Дані вантажить батьківський ProjectsView;
// тут лише розмітка таблиці й тогл is_sync (перенесено з TimeCampView).
import { computed } from 'vue'

import DataTable from '@/components/data/DataTable.vue'
import type { Column } from '@/components/data/types'
import Badge from '@/components/ui/Badge.vue'
import Icon from '@/components/ui/Icon.vue'
import Toggle from '@/components/ui/Toggle.vue'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()

const cols = computed<Column[]>(() => [
  { key: 'name', label: t.value.col_name },
  { key: 'issue_key', label: t.value.col_mapping },
  { key: 'entries_count', label: t.value.col_entries, align: 'right', mono: true, width: 90 },
  { key: 'is_sync', label: t.value.col_sync_on, align: 'right', width: 90 },
])
</script>

<template>
  <DataTable :columns="cols" :rows="store.tcProjects" :get-id="(r) => r.id" :empty="t.empty">
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
</template>
