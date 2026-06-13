<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'

import DataPage from '@/components/data/DataPage.vue'
import SyncBtn from '@/components/data/SyncBtn.vue'
import type { TabItem } from '@/components/data/types'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()
const route = useRoute()
const router = useRouter()

// Дані вантажить кожна під-вʼюха сама (D10) — ProjectsView лише каркас. Закладки
// (TimeCamp/Jira) — окремі routed-під-сторінки; DataPage рендерить смугу і
// сигналізує вибір, навігацію робить ця в'юха. Лічильники ліниві.
const tabs = computed<TabItem[]>(() => [
  {
    id: 'projects-timecamp',
    label: t.value.nav_projects_timecamp,
    icon: 'clock',
    count: store.tcProjectsLoaded ? store.tcProjects.length : undefined,
  },
  {
    id: 'projects-jira',
    label: t.value.nav_projects_jira,
    icon: 'inbox',
    count: store.jrProjectsLoaded ? store.jrProjects.length : undefined,
  },
])

const active = computed<string>(() => (route.name as string) ?? 'projects-timecamp')

// Кнопка синку синкає лише сервіс активної під-вʼюхи (TimeCamp ↔ Jira).
const activeService = computed<'tc' | 'jr'>(() =>
  route.name === 'projects-jira' ? 'jr' : 'tc',
)
function syncActive(): Promise<void> {
  return store.syncProjects(activeService.value)
}

function go(name: string): void {
  if (name !== route.name) void router.push({ name })
}
</script>

<template>
  <DataPage
    :title="t.pr_title"
    :desc="t.pr_desc"
    :error="store.error"
    :tabs="tabs"
    :active-tab="active"
    @update:active-tab="go"
  >
    <template #actions>
      <SyncBtn :label="t.pr_sync_projects" icon="sync" :action="syncActive" />
    </template>

    <RouterView />
  </DataPage>
</template>
