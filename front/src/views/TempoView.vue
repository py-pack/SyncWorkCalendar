<script setup lang="ts">
// Контейнер екрана /tempo (rework-tempo-screen, D1). DataPage з двома вкладками
// (router-agnostic, як ProjectsView): «Tempo» (реальні jr_worklogs) і «Конвеєр
// синку» (worklog_sync_tasks). Дані вантажить кожна під-вʼюха сама; контейнер дає
// заголовок, закладки і агрегатну дію «Забрати з Tempo» (лише на вкладці Tempo).
import { computed, ref } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'

import DataPage from '@/components/data/DataPage.vue'
import type { TabItem } from '@/components/data/types'
import PullWorklogsModal from '@/components/tempo/PullWorklogsModal.vue'
import Btn from '@/components/ui/Btn.vue'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()
const route = useRoute()
const router = useRouter()

const tabs = computed<TabItem[]>(() => [
  {
    id: 'tempo-worklogs',
    label: t.value.nav_tempo_worklogs,
    icon: 'sync',
    count: store.tempoTotal || undefined,
  },
  {
    id: 'tempo-pipeline',
    label: t.value.nav_tempo_pipeline,
    icon: 'bolt',
    count: store.wstTotal || undefined,
  },
])

const active = computed<string>(() => (route.name as string) ?? 'tempo-worklogs')
const desc = computed(() =>
  active.value === 'tempo-pipeline' ? t.value.tempo_pipeline_desc : t.value.tempo_worklogs_desc,
)

const pullOpen = ref(false)

function go(name: string): void {
  if (name !== route.name) void router.push({ name })
}
</script>

<template>
  <DataPage
    :title="t.tempo_title"
    :desc="desc"
    :error="store.error"
    :tabs="tabs"
    :active-tab="active"
    @update:active-tab="go"
  >
    <template v-if="active === 'tempo-worklogs'" #actions>
      <Btn variant="default" size="sm" icon="cloudDown" @click="pullOpen = true">
        {{ t.tmp_pull }}
      </Btn>
    </template>

    <RouterView />

    <PullWorklogsModal :open="pullOpen" @close="pullOpen = false" />
  </DataPage>
</template>
