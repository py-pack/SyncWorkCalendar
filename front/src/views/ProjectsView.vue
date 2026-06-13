<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'

import PageHeader from '@/components/data/PageHeader.vue'
import Tabs from '@/components/data/Tabs.vue'
import type { TabItem } from '@/components/data/types'
import Icon from '@/components/ui/Icon.vue'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()
const route = useRoute()
const router = useRouter()

// Активна під-вʼюха визначається маршрутом (а не локальним ref), тож URL завжди
// відображає показане джерело проектів (/projects/timecamp ↔ /projects/jira).
const tabs = computed<TabItem[]>(() => [
  {
    id: 'projects-timecamp',
    label: t.value.nav_projects_timecamp,
    icon: 'clock',
    count: store.tcProjects.length,
  },
  {
    id: 'projects-jira',
    label: t.value.nav_projects_jira,
    icon: 'inbox',
    count: store.jrProjects.length,
  },
])

const active = computed<string>(() => (route.name as string) ?? 'projects-timecamp')

function go(name: string): void {
  if (name !== route.name) void router.push({ name })
}

onMounted(async () => {
  await store.loadProjects() // дані з БД одразу
  void store.autoSyncProjects() // у фоні освіжаємо проекти TimeCamp + Jira
})
</script>

<template>
  <div class="page">
    <PageHeader :title="t.pr_title" :desc="t.pr_desc" />

    <Tabs :model-value="active" :tabs="tabs" @update:model-value="go" />

    <p v-if="store.error" class="data-error"><Icon name="alert" :size="15" />{{ store.error }}</p>

    <div class="page__body">
      <RouterView />
    </div>
  </div>
</template>
