<script setup lang="ts">
// Під-вʼюха «Проекти → Jira» (rework-jira-projects-subview).
// Власний запит при відкритті (лише GET /jr-projects, ідемпотентно). Плоский
// список (Jira-проекти не мають parent_id/color). Фільтр за станом синку
// (is_watched) і швидкий пошук — клієнтські, по локальних даних. Налаштування
// синку — у попапі (шестерня / подвійний клік), без інлайн-тогла.
import { computed, onMounted, ref } from 'vue'

import type { JRProject } from '@/api/types'
import JrSyncSettingsModal from '@/components/projects/JrSyncSettingsModal.vue'
import Badge from '@/components/ui/Badge.vue'
import Icon from '@/components/ui/Icon.vue'
import IconBtn from '@/components/ui/IconBtn.vue'
import Segmented from '@/components/ui/Segmented.vue'
import type { SegmentedOption } from '@/components/ui/types'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()

type Active = 'active' | 'inactive' | 'all'

const filterOpts = computed<SegmentedOption[]>(() => [
  { value: 'all', label: t.value.flt_all },
  { value: 'active', label: t.value.flt_active },
  { value: 'inactive', label: t.value.flt_inactive },
])

const query = ref('')

// Фільтр (за is_watched) + швидкий пошук — обидва по вже завантажених локальних
// даних, без re-fetch.
const filtered = computed<JRProject[]>(() => {
  let list = store.jrProjects
  if (store.jrActive === 'active') list = list.filter((p) => p.is_watched)
  else if (store.jrActive === 'inactive') list = list.filter((p) => !p.is_watched)

  const q = query.value.trim().toLowerCase()
  if (q) {
    list = list.filter(
      (p) => p.key.toLowerCase().includes(q) || p.name.toLowerCase().includes(q),
    )
  }
  return list
})

function onFilter(v: string): void {
  store.jrActive = v as Active
}

const editing = ref<JRProject | null>(null)
function openSettings(p: JRProject): void {
  editing.value = p
}

onMounted(() => {
  void store.loadJrProjects()
})
</script>

<template>
  <div class="tct-wrap">
    <div class="tct-bar">
      <Segmented
        :model-value="store.jrActive"
        :options="filterOpts"
        size="sm"
        @update:model-value="onFilter"
      />
      <span class="spacer" />
      <label class="tct-search">
        <Icon name="search" :size="15" />
        <input v-model="query" class="sw-input tct-search__input" :placeholder="t.search" />
      </label>
    </div>

    <div class="tct">
      <div v-if="!filtered.length" class="tct__empty">{{ t.empty }}</div>

      <div
        v-for="p in filtered"
        :key="p.id"
        class="tct__row"
        :class="{ 'is-archived': p.is_archived }"
        @dblclick="openSettings(p)"
      >
        <span class="mono key-pill">{{ p.key }}</span>
        <span class="tct__name">{{ p.name }}</span>
        <Badge v-if="p.is_archived" tone="neutral" soft>{{ t.col_archived }}</Badge>

        <span class="spacer" />

        <span class="tct__count" :title="t.col_issues">
          <Icon name="list" :size="13" />{{ p.issues_count }}
        </span>
        <span class="tct__state" :class="{ 'is-on': p.is_watched }">
          <span class="tct__statedot" />
          {{ p.is_watched ? t.sync_state_on : t.sync_state_off }}
        </span>
        <IconBtn name="settings" size="sm" :title="t.settings" @click="openSettings(p)" />
      </div>
    </div>

    <JrSyncSettingsModal :project="editing" @close="editing = null" />
  </div>
</template>
