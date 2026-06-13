<script setup lang="ts">
import { computed, onMounted } from 'vue'

import DataTable from '@/components/data/DataTable.vue'
import PageHeader from '@/components/data/PageHeader.vue'
import type { Column } from '@/components/data/types'
import Btn from '@/components/ui/Btn.vue'
import Icon from '@/components/ui/Icon.vue'
import { useI18n } from '@/i18n'
import { durationMin, fmtDur } from '@/lib/format'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()

// Лише незіставлені записи — проекти винесено в окремий екран «Проекти».
const cols = computed<Column[]>(() => [
  { key: 'description', label: t.value.col_desc },
  { key: 'tc_project_name', label: t.value.col_project },
  { key: 'start_at', label: t.value.col_date, mono: true, width: 130 },
  { key: 'dur', label: t.value.col_duration, align: 'right', mono: true, width: 90 },
  { key: 'act', label: '', align: 'right', width: 120 },
])

onMounted(async () => {
  await store.loadUntracked() // дані з БД одразу
  void store.autoSyncEntries() // у фоні освіжаємо записи з TimeCamp
})
</script>

<template>
  <div class="page">
    <PageHeader :title="t.tc_title" :desc="t.tc_desc" />

    <p v-if="store.error" class="data-error"><Icon name="alert" :size="15" />{{ store.error }}</p>

    <div class="page__body">
      <DataTable
        :columns="cols"
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
