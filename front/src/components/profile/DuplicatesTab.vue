<script setup lang="ts">
// Закладка «Дублі» (frontend-profile, capability api-worklog-dedup): групи
// дубльованих Tempo-worklog-ів за період + масова чистка. Синхронно (як попапи
// синку): спінер на кнопках, підсумок, перезавантаження. «Оновити з Tempo» —
// наявний пул worklog-ів (`POST /sync/jira/worklogs`) перед чисткою (D8).
import { computed, onMounted, ref, watch } from 'vue'

import { api } from '@/api/client'
import {
  ApiError,
  type Period,
  type WorklogDedupResult,
  type WorklogDuplicateGroup,
} from '@/api/types'
import PeriodPicker from '@/components/data/PeriodPicker.vue'
import Btn from '@/components/ui/Btn.vue'
import Icon from '@/components/ui/Icon.vue'
import Spinner from '@/components/ui/Spinner.vue'
import { useI18n } from '@/i18n'
import { fmtDateTime, secToHm } from '@/lib/format'
import { syncPeriod } from '@/lib/period'

const { t } = useI18n()

const period = ref<Period>(syncPeriod())
const groups = ref<WorklogDuplicateGroup[]>([])
const selected = ref<Set<string>>(new Set())
const loading = ref(false)
const error = ref('')
const fixing = ref(false)
const refreshing = ref(false)
const summary = ref<WorklogDedupResult | null>(null)

/** Стабільний ключ групи (ключ дедупу) для вибору/`v-for`. */
function groupKey(g: WorklogDuplicateGroup): string {
  return `${g.jr_issues_id}|${g.started_at}|${g.duration}`
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const res = await api.worklogDuplicates(period.value)
    groups.value = res.groups
    selected.value = new Set()
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : String(e)
    groups.value = []
  } finally {
    loading.value = false
  }
}

function toggle(g: WorklogDuplicateGroup): void {
  const k = groupKey(g)
  const n = new Set(selected.value)
  n.has(k) ? n.delete(k) : n.add(k)
  selected.value = n
}

// «Обрати всі»: усі групи обрані / частина (indeterminate) / жодної.
const allSelected = computed(
  () => groups.value.length > 0 && groups.value.every((g) => selected.value.has(groupKey(g))),
)
const someSelected = computed(() => selected.value.size > 0)
function toggleAll(): void {
  selected.value = allSelected.value ? new Set() : new Set(groups.value.map(groupKey))
}

/** Синхронізувати дзеркало `jr_worklogs` перед чисткою (актуальний стан Tempo). */
async function refreshFromTempo(): Promise<void> {
  if (refreshing.value || fixing.value) return
  refreshing.value = true
  error.value = ''
  summary.value = null
  try {
    await api.syncJrWorklogs(period.value)
    await load()
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : String(e)
  } finally {
    refreshing.value = false
  }
}

/** Реальне видалення зайвих із Tempo по обраних групах (незворотно). */
async function fixSelected(): Promise<void> {
  if (fixing.value || refreshing.value || selected.value.size === 0) return
  fixing.value = true
  error.value = ''
  summary.value = null
  const chosen = groups.value.filter((g) => selected.value.has(groupKey(g)))
  const payload = chosen.map((g) => g.members.map((m) => m.id))
  try {
    summary.value = await api.dedupWorklogs(payload)
    await load()
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : String(e)
  } finally {
    fixing.value = false
  }
}

watch(period, () => void load())
onMounted(() => void load())
</script>

<template>
  <div class="dups">
    <p class="dups__hint">{{ t.dup_hint }}</p>

    <div class="dups__bar">
      <label class="dups__selall">
        <input
          type="checkbox"
          :checked="allSelected"
          :indeterminate.prop="someSelected && !allSelected"
          :disabled="!groups.length"
          @change="toggleAll"
        />
        {{ t.dup_select_all }}
        <span v-if="groups.length" class="dups__selcount">{{ selected.size }}/{{ groups.length }}</span>
      </label>
      <PeriodPicker :model-value="period" @update:model-value="period = $event" />
      <span class="spacer" />
      <Btn variant="default" icon="cloudDown" :disabled="refreshing || fixing" @click="refreshFromTempo">
        <Spinner v-if="refreshing" :size="14" />
        <template v-else>{{ t.dup_refresh }}</template>
      </Btn>
      <Btn
        variant="primary"
        icon="trash"
        :disabled="fixing || refreshing || selected.size === 0"
        @click="fixSelected"
      >
        <Spinner v-if="fixing" :size="14" />
        <template v-else>{{ t.dup_fix_selected }}</template>
      </Btn>
    </div>

    <p v-if="error" class="data-error"><Icon name="alert" />{{ error }}</p>

    <p v-if="summary" class="dups__summary">
      {{ t.dup_deleted }} <b>{{ summary.deleted }}</b> · {{ t.dup_kept }} <b>{{ summary.kept }}</b>
      <span v-if="summary.errors.length"> · {{ t.dup_errors }} <b>{{ summary.errors.length }}</b></span>
    </p>

    <div v-if="loading" class="dups__state"><Spinner :size="18" /></div>
    <div v-else-if="groups.length === 0" class="dups__state dups__empty">
      <Icon name="check" :size="28" :stroke="1.4" />
      <p>{{ t.dup_empty }}</p>
    </div>

    <ul v-else class="dups__list">
      <li
        v-for="g in groups"
        :key="groupKey(g)"
        :class="['dups__grp', { 'is-on': selected.has(groupKey(g)) }]"
      >
        <label class="dups__head">
          <input type="checkbox" :checked="selected.has(groupKey(g))" @change="toggle(g)" />
          <span class="dups__task">
            <span class="mono dups__key">{{ g.issue_key || '—' }}</span>
            <span v-if="g.issue_name" class="dups__name">{{ g.issue_name }}</span>
          </span>
          <span class="dups__meta mono">{{ fmtDateTime(g.started_at) }} · {{ secToHm(g.duration) }}</span>
          <span class="dups__count">×{{ g.count }}</span>
        </label>
        <ul class="dups__members">
          <li v-for="m in g.members" :key="m.id" class="dups__member">
            <span class="mono dups__mid">#{{ m.id }}</span>
            <span v-if="m.is_linked" class="dups__linked">{{ t.dup_linked }}</span>
            <span class="dups__desc">{{ m.description || '—' }}</span>
          </li>
        </ul>
      </li>
    </ul>
  </div>
</template>
