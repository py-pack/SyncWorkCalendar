<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import type { Period } from '@/api/types'
import DataPage from '@/components/data/DataPage.vue'
import DataTable from '@/components/data/DataTable.vue'
import FilterSelect from '@/components/data/FilterSelect.vue'
import PeriodPicker from '@/components/data/PeriodPicker.vue'
import ProjTag from '@/components/data/ProjTag.vue'
import type { Column } from '@/components/data/types'
import SyncIssuesModal from '@/components/jira/SyncIssuesModal.vue'
import Badge from '@/components/ui/Badge.vue'
import Btn from '@/components/ui/Btn.vue'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()

// Задачі з локальної БД за період створення (без вкладок) — проекти на екрані
// «Проекти». Порядок колонок: Проект → Тип → Статус → Номер (key) → Опис.
const cols = computed<Column[]>(() => [
  { key: 'project', label: t.value.col_project, width: 160 },
  { key: 'type', label: t.value.col_type, width: 110 },
  { key: 'status', label: t.value.col_status, width: 150 },
  { key: 'key', label: t.value.col_key, width: 120 },
  { key: 'name', label: t.value.col_desc },
])

// id → key проекту (для кольорового тегу задачі); jrProjects вантажиться в
// loadJrIssues() разом із першою сторінкою.
const projKeyById = computed<Record<number, string>>(() => {
  const map: Record<number, string> = {}
  for (const p of store.jrProjects) map[p.id] = p.key
  return map
})

// Опції випадайок фільтрів. Проекти — лише ті, що в синку (`is_watched`):
// фільтрувати за проектами, які не синкаються, сенсу немає.
const projectOptions = computed(() =>
  store.jrProjects
    .filter((p) => p.is_watched)
    .map((p) => ({
      value: String(p.id),
      label: `${p.key} — ${p.name}`,
      dim: p.is_archived,
    })),
)
const statusOptions = computed(() => store.jrStatusOptions.map((s) => ({ value: s, label: s })))
const selectedProject = computed(() =>
  store.jrProjectFilter === null ? null : String(store.jrProjectFilter),
)

type Tone = 'neutral' | 'green' | 'amber' | 'accent'
function statusTone(s: string): Tone {
  if (s === 'Done') return 'green'
  if (s === 'To Do') return 'neutral'
  if (s === 'In Review') return 'amber'
  return 'accent'
}

// --- фільтри ---------------------------------------------------------------
function onPeriod(p: Period): void {
  void store.setJrPeriod(p)
}
function onProject(v: string | null): void {
  void store.setJrProjectFilter(v === null ? null : Number(v))
}
function onStatus(v: string | null): void {
  void store.setJrStatus(v)
}

// Пошук за назвою — з debounce, щоб не бити сервер на кожну літеру.
const queryInput = ref(store.jrQuery)
let timer: ReturnType<typeof setTimeout> | undefined
watch(queryInput, (q) => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => void store.setJrQuery(q.trim()), 300)
})
onBeforeUnmount(() => {
  if (timer) clearTimeout(timer)
})

// --- пагінація -------------------------------------------------------------
const canPrev = computed(() => store.jrOffset > 0)
const canNext = computed(() => store.jrOffset + store.jrPageSize < store.jrTotal)
const pageInfo = computed(() => {
  const from = store.jrTotal === 0 ? 0 : store.jrOffset + 1
  const to = Math.min(store.jrOffset + store.jrPageSize, store.jrTotal)
  return `${from}–${to} / ${store.jrTotal}`
})
function prev(): void {
  void store.setJrOffset(store.jrOffset - store.jrPageSize)
}
function next(): void {
  void store.setJrOffset(store.jrOffset + store.jrPageSize)
}

// --- попап витягу задач за період -------------------------------------------
const syncOpen = ref(false)

// Лише читання з БД при відкритті — жодного авто-синку (D1).
onMounted(() => void store.loadJrIssues())
</script>

<template>
  <DataPage :title="t.jr_title" :desc="t.jr_desc" :error="store.error">
    <template #actions>
      <Btn variant="default" size="sm" icon="cloudDown" @click="syncOpen = true">
        {{ t.jr_sync }}
      </Btn>
    </template>

    <template #toolbar>
      <div class="pipe jrbar">
        <PeriodPicker :model-value="store.jrPeriod" @update:model-value="onPeriod" />
        <FilterSelect
          :model-value="selectedProject"
          :options="projectOptions"
          :all-label="t.jr_flt_project"
          :placeholder="t.search"
          searchable
          @update:model-value="onProject"
        />
        <FilterSelect
          :model-value="store.jrStatus"
          :options="statusOptions"
          :all-label="t.jr_flt_status"
          @update:model-value="onStatus"
        />
        <input v-model="queryInput" class="sw-input jrbar__search" :placeholder="t.jr_flt_search" />
      </div>
    </template>

    <DataTable :columns="cols" :rows="store.jrIssues" :get-id="(r) => r.id" :empty="t.empty">
      <template #cell-project="{ row }">
        <ProjTag :label="projKeyById[row.jr_project_id] ?? String(row.jr_project_id)" />
      </template>
      <template #cell-status="{ row }">
        <Badge :tone="statusTone(row.status)" soft dot>{{ row.status }}</Badge>
      </template>
      <template #cell-key="{ row }">
        <span class="mono key-pill">{{ row.key }}</span>
      </template>
      <template #cell-name="{ row }">
        <span :class="{ faint: !row.active }">{{ row.name }}</span>
      </template>
    </DataTable>

    <div v-if="store.jrTotal > store.jrPageSize" class="tcpage">
      <Btn size="sm" variant="ghost" icon="chevL" :disabled="!canPrev" @click="prev">
        {{ t.page_prev }}
      </Btn>
      <span class="tcpage__pos mono">{{ pageInfo }}</span>
      <Btn size="sm" variant="ghost" icon-right="chevR" :disabled="!canNext" @click="next">
        {{ t.page_next }}
      </Btn>
    </div>

    <SyncIssuesModal :open="syncOpen" @close="syncOpen = false" />
  </DataPage>
</template>
