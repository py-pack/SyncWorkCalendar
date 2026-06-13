<script setup lang="ts">
// Під-вʼюха «Проекти → TimeCamp» (rework-projects-screen).
// Власний запит при відкритті (лише GET /tc-projects — усі проекти); дерево за
// parent_id з кольоровим акцентом; архівні тьмяні. Маппінг — кольоровий тег
// задачі ОДРАЗУ біля назви. Фільтр (за станом синку is_sync) і швидкий пошук —
// клієнтські, по локальних даних. Налаштування синку — у попапі (шестерня /
// подвійний клік), без інлайн-тогла.
import { computed, onMounted, ref } from 'vue'

import type { TCProject } from '@/api/types'
import SyncSettingsModal from '@/components/projects/SyncSettingsModal.vue'
import Badge from '@/components/ui/Badge.vue'
import Icon from '@/components/ui/Icon.vue'
import IconBtn from '@/components/ui/IconBtn.vue'
import Segmented from '@/components/ui/Segmented.vue'
import type { SegmentedOption } from '@/components/ui/types'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'
import { buildTree, flattenTree, safeColor } from '@/lib/tree'

const { t } = useI18n()
const store = useTablesStore()

type Active = 'active' | 'inactive' | 'all'

const filterOpts = computed<SegmentedOption[]>(() => [
  { value: 'all', label: t.value.flt_all },
  { value: 'active', label: t.value.flt_active },
  { value: 'inactive', label: t.value.flt_inactive },
])

const query = ref('')

// Фільтр (за is_sync) + швидкий пошук — обидва по вже завантажених локальних
// даних, без re-fetch. Дерево будується з відфільтрованого списку (вузол із
// відфільтрованим батьком піднімається в корінь — orphan-hoisting у buildTree).
const filtered = computed<TCProject[]>(() => {
  let list = store.tcProjects
  if (store.tcActive === 'active') list = list.filter((p) => p.is_sync)
  else if (store.tcActive === 'inactive') list = list.filter((p) => !p.is_sync)

  const q = query.value.trim().toLowerCase()
  if (q) {
    list = list.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        (p.issue_key?.toLowerCase().includes(q) ?? false) ||
        (p.issue_name?.toLowerCase().includes(q) ?? false),
    )
  }
  return list
})

const flat = computed(() => flattenTree(buildTree(filtered.value)))

function onFilter(v: string): void {
  store.tcActive = v as Active
}

function colorVar(c: string | null): Record<string, string> {
  const safe = safeColor(c)
  return safe ? { '--proj': safe } : {}
}

const editing = ref<TCProject | null>(null)
function openSettings(p: TCProject): void {
  editing.value = p
}

onMounted(() => {
  void store.loadTcProjects()
})
</script>

<template>
  <div class="tct-wrap">
    <div class="tct-bar">
      <Segmented
        :model-value="store.tcActive"
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
      <div v-if="!flat.length" class="tct__empty">{{ t.empty }}</div>

      <div
        v-for="n in flat"
        :key="n.item.id"
        class="tct__row"
        :class="{ 'is-archived': n.item.is_archived }"
        :style="{ paddingLeft: `${14 + n.depth * 22}px`, ...colorVar(n.item.color) }"
        @dblclick="openSettings(n.item)"
      >
        <span class="tct__dot" />
        <span class="tct__name">
          <span class="mono tct__id">#{{ n.item.id }}</span>
          {{ n.item.name }}
        </span>

        <!-- маппінг — одразу біля назви -->
        <span
          v-if="n.item.issue_key"
          class="tct__tag"
          :class="{ 'is-dim': n.item.issue_active === false }"
        >
          <span class="tct__tagdot" />
          <span class="mono">{{ n.item.issue_key }}</span>
          <span v-if="n.item.issue_name" class="tct__tagname">{{ n.item.issue_name }}</span>
        </span>
        <span v-else class="faint tct__nomap">—</span>

        <span class="spacer" />

        <Badge v-if="n.item.is_archived" tone="neutral" soft>{{ t.col_archived }}</Badge>
        <span class="tct__state" :class="{ 'is-on': n.item.is_sync }">
          <span class="tct__statedot" />
          {{ n.item.is_sync ? t.sync_state_on : t.sync_state_off }}
        </span>
        <IconBtn name="settings" size="sm" :title="t.settings" @click="openSettings(n.item)" />
      </div>
    </div>

    <SyncSettingsModal :project="editing" @close="editing = null" />
  </div>
</template>
