<script setup lang="ts">
// Під-вʼюха «Проекти → Jira» (rework-jira-projects-subview).
// Власний запит при відкритті (лише GET /jr-projects, ідемпотентно). Плоский
// список (Jira-проекти не мають parent_id/color). Фільтр за станом синку
// (is_watched) і швидкий пошук — клієнтські, по локальних даних. Налаштування
// синку — у попапі (шестерня / подвійний клік), без інлайн-тогла.
import { computed, onMounted, ref } from 'vue'

import type { JRProject } from '@/api/types'
import SyncFilter from '@/components/data/SyncFilter.vue'
import SyncState from '@/components/data/SyncState.vue'
import JrSyncSettingsModal from '@/components/projects/JrSyncSettingsModal.vue'
import Badge from '@/components/ui/Badge.vue'
import Icon from '@/components/ui/Icon.vue'
import IconBtn from '@/components/ui/IconBtn.vue'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'

const { t } = useI18n()
const store = useTablesStore()

const query = ref('')

// Фільтр (за is_watched) + швидкий пошук — обидва по вже завантажених локальних
// даних, без re-fetch.
const filtered = computed<JRProject[]>(() => {
  let list = store.jrProjects
  if (store.jrActive === 'synced') list = list.filter((p) => p.is_watched)
  else if (store.jrActive === 'unsynced') list = list.filter((p) => !p.is_watched)

  const q = query.value.trim().toLowerCase()
  if (q) {
    list = list.filter(
      (p) => p.key.toLowerCase().includes(q) || p.name.toLowerCase().includes(q),
    )
  }
  return list
})

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
      <SyncFilter :model-value="store.jrActive" @update:model-value="store.jrActive = $event" />
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
        <SyncState :synced="p.is_watched" />
        <IconBtn name="settings" size="sm" :title="t.settings" @click="openSettings(p)" />
      </div>
    </div>

    <JrSyncSettingsModal :project="editing" @close="editing = null" />
  </div>
</template>
