<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'

import PageHeader from '@/components/data/PageHeader.vue'
import SyncBtn from '@/components/data/SyncBtn.vue'
import Tabs from '@/components/data/Tabs.vue'
import type { TabItem } from '@/components/data/types'
import Icon from '@/components/ui/Icon.vue'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()
const route = useRoute()
const router = useRouter()

// Дані вантажить кожна під-вʼюха сама (D10) — ProjectsView лише каркас. Жодного
// авто-синку: синхронізація проектів — окрема явна кнопка (D9). Лічильники вкладок
// ліниві — badge лише для вже завантаженого джерела.
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

function go(name: string): void {
  if (name !== route.name) void router.push({ name })
}
</script>

<template>
  <div class="page">
    <PageHeader :title="t.pr_title" :desc="t.pr_desc">
      <template #actions>
        <SyncBtn :label="t.pr_sync_projects" icon="sync" :action="store.syncProjects" />
      </template>
    </PageHeader>

    <Tabs :model-value="active" :tabs="tabs" @update:model-value="go" />

    <p v-if="store.error" class="data-error"><Icon name="alert" :size="15" />{{ store.error }}</p>

    <div class="page__body">
      <RouterView />
    </div>
  </div>
</template>
