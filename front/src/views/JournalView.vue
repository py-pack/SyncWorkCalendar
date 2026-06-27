<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import type { ApiJobStatus, Period } from '@/api/types'
import DataPage from '@/components/data/DataPage.vue'
import DataTable from '@/components/data/DataTable.vue'
import FilterSelect from '@/components/data/FilterSelect.vue'
import PeriodPicker from '@/components/data/PeriodPicker.vue'
import StatusBadge from '@/components/data/StatusBadge.vue'
import type { Column } from '@/components/data/types'
import Badge from '@/components/ui/Badge.vue'
import Btn from '@/components/ui/Btn.vue'
import Icon from '@/components/ui/Icon.vue'
import Sheet from '@/components/ui/Sheet.vue'
import Spinner from '@/components/ui/Spinner.vue'
import { useI18n } from '@/i18n'
import { fmtDateTime } from '@/lib/format'
import { useJournalStore } from '@/stores/journal'

const { t } = useI18n()
const store = useJournalStore()

// Статичний перелік відомих імен sync-тригерів (константи беку — стабільні).
const SYNC_TRIGGERS = [
  'sync.timecamp.projects',
  'sync.timecamp.entries',
  'sync.jira.projects',
  'sync.jira.issues',
  'sync.jira.issues-all',
  'sync.jira.worklogs',
  'sync.worklog-tasks.prepare',
  'sync.worklog-tasks.resolve-issues',
  'sync.worklog-tasks.push-to-tempo',
  'sync.worklog-tasks.push-one',
  'sync.reconcile-links',
] as const

const statusOptions = computed(() => [
  { value: 'running', label: t.value.s_running },
  { value: 'needs_verification', label: t.value.s_needs_verification },
  { value: 'verified', label: t.value.s_verified },
  { value: 'failed', label: t.value.s_failed },
])
const triggerOptions = SYNC_TRIGGERS.map((tr) => ({ value: tr, label: tr }))

// Зведення лічильників по статусах (з store.summary) — компактні чипи в тулбарі.
const summaryChips = computed(() => [
  { key: 'running', tone: 'accent', label: t.value.s_running, count: store.summary.running },
  { key: 'needs_verification', tone: 'amber', label: t.value.s_needs_verification, count: store.summary.needs_verification },
  { key: 'verified', tone: 'green', label: t.value.s_verified, count: store.summary.verified },
  { key: 'failed', tone: 'red', label: t.value.s_failed, count: store.summary.failed },
])

const cols = computed<Column[]>(() => [
  { key: 'id', label: 'ID', width: 90, mono: true },
  { key: 'trigger_name', label: t.value.job_trigger },
  { key: 'status', label: t.value.col_status, width: 170 },
  { key: 'started_at', label: t.value.job_started, width: 170, mono: true },
  { key: 'created_by', label: t.value.job_by, width: 120, mono: true },
  { key: 'act', label: '', align: 'right', width: 130 },
])

// --- фільтри ---------------------------------------------------------------
function onPeriod(p: Period): void {
  void store.setPeriod(p)
}
function onStatus(v: string | null): void {
  void store.setStatusFilter(v as ApiJobStatus | null)
}
function onTrigger(v: string | null): void {
  void store.setTriggerFilter(v)
}

// --- пагінація -------------------------------------------------------------
const canPrev = computed(() => store.offset > 0)
const canNext = computed(() => store.offset + store.pageSize < store.total)
const pageInfo = computed(() => {
  const from = store.total === 0 ? 0 : store.offset + 1
  const to = Math.min(store.offset + store.pageSize, store.total)
  return `${from}–${to} / ${store.total}`
})
function prev(): void {
  void store.setOffset(store.offset - store.pageSize)
}
function next(): void {
  void store.setOffset(store.offset + store.pageSize)
}

function prettyJson(value: unknown): string {
  return JSON.stringify(value, null, 2)
}

// --- ретрай: pending-стан по id рядка (спінер + disabled під час запиту) -----
// Це фронтовий guard від подвійного кліку; бекендний CAS — друга лінія оборони
// (паралельний клік → 409). `store.retry` сам ковтає помилку у банер, тож тут
// лише тримаємо видимий pending до завершення запиту (успіх чи помилка).
const retrying = ref<Set<string>>(new Set())
async function onRetry(id: string): Promise<void> {
  if (retrying.value.has(id)) return
  retrying.value.add(id)
  try {
    await store.retry(id)
  } finally {
    retrying.value.delete(id)
  }
}

// Лише читання з БД при відкритті — журнал сам є логом синків (D6).
onMounted(() => void store.load())
</script>

<template>
  <DataPage :title="t.jr_journal_title" :desc="t.jr_journal_desc" :error="store.error">
    <template #actions>
      <Btn
        variant="primary"
        icon="check"
        :disabled="store.summary.needs_verification === 0"
        :title="t.job_verify_all_hint"
        @click="store.verifyAll()"
      >
        {{ t.job_verify_all }}
      </Btn>
    </template>

    <template #toolbar>
      <div class="pipe jrbar">
        <PeriodPicker :model-value="store.period" @update:model-value="onPeriod" />
        <FilterSelect
          :model-value="store.statusFilter"
          :options="statusOptions"
          :all-label="t.job_flt_status"
          @update:model-value="onStatus"
        />
        <FilterSelect
          :model-value="store.triggerFilter"
          :options="triggerOptions"
          :all-label="t.job_flt_trigger"
          :placeholder="t.search"
          searchable
          @update:model-value="onTrigger"
        />
        <div class="jrsum">
          <span
            v-for="c in summaryChips"
            :key="c.key"
            class="jrsum__chip"
            :class="`is-${c.tone}`"
          >
            <span class="jrsum__dot" />{{ c.label }}<b>{{ c.count }}</b>
          </span>
        </div>
      </div>
    </template>

    <DataTable
        :columns="cols"
        :rows="store.jobs"
        :get-id="(r) => r.id"
        row-clickable
        :empty="t.empty"
        @row-click="(r) => store.open(r.id)"
      >
        <template #cell-id="{ row }">{{ row.id.slice(0, 8) }}</template>
        <template #cell-trigger_name="{ row }">
          <span class="mono job-trig"><Icon name="bolt" :size="13" />{{ row.trigger_name }}</span>
        </template>
        <template #cell-status="{ row }">
          <Badge v-if="row.status === 'running'" tone="accent" soft>
            <Spinner :size="11" />{{ t.s_running }}
          </Badge>
          <StatusBadge v-else :status="row.status" />
        </template>
        <template #cell-started_at="{ row }">{{ fmtDateTime(row.started_at) }}</template>
        <template #cell-act="{ row }">
          <Btn
            v-if="row.status === 'needs_verification'"
            size="sm"
            variant="primary"
            icon="check"
            @click.stop="store.verify(row.id)"
          >
            {{ t.job_verify }}
          </Btn>
          <Btn
            v-else-if="row.status === 'failed'"
            size="sm"
            variant="soft"
            :icon="retrying.has(row.id) ? undefined : 'sync'"
            :disabled="retrying.has(row.id)"
            @click.stop="onRetry(row.id)"
          >
            <Spinner v-if="retrying.has(row.id)" :size="14" />
            <template v-else>{{ t.job_retry }}</template>
          </Btn>
          <Icon v-else name="chevR" :size="16" />
        </template>
      </DataTable>

    <div v-if="store.total > store.pageSize" class="tcpage">
      <Btn size="sm" variant="ghost" icon="chevL" :disabled="!canPrev" @click="prev">
        {{ t.page_prev }}
      </Btn>
      <span class="tcpage__pos mono">{{ pageInfo }}</span>
      <Btn size="sm" variant="ghost" icon-right="chevR" :disabled="!canNext" @click="next">
        {{ t.page_next }}
      </Btn>
    </div>

    <Sheet
      :open="!!store.detail"
      :title="store.detail ? store.detail.id : ''"
      :width="420"
      @close="store.close()"
    >
      <div v-if="store.detail" class="jobdet">
        <div class="jobdet__row">
          <span class="mono job-trig"><Icon name="bolt" :size="14" />{{ store.detail.trigger_name }}</span>
        </div>
        <div class="jobdet__grid">
          <div>
            <span class="muted">{{ t.col_status }}</span>
            <Badge v-if="store.detail.status === 'running'" tone="accent" soft>
              <Spinner :size="11" />{{ t.s_running }}
            </Badge>
            <StatusBadge v-else :status="store.detail.status" />
          </div>
          <div><span class="muted">{{ t.job_by }}</span><span class="mono">{{ store.detail.created_by }}</span></div>
          <div><span class="muted">{{ t.job_started }}</span><span class="mono">{{ fmtDateTime(store.detail.started_at) }}</span></div>
          <div><span class="muted">{{ t.job_finished }}</span><span class="mono">{{ store.detail.finished_at ? fmtDateTime(store.detail.finished_at) : '—' }}</span></div>
          <div><span class="muted">{{ t.job_verified_by }}</span><span class="mono">{{ store.detail.verified_by || '—' }}</span></div>
          <div><span class="muted">{{ t.job_verified_at }}</span><span class="mono">{{ store.detail.verified_at ? fmtDateTime(store.detail.verified_at) : '—' }}</span></div>
        </div>

        <div class="jobdet__sec">
          <div class="jobdet__lbl">{{ t.job_payload }}</div>
          <pre class="jobdet__json mono">{{ prettyJson(store.detail.payload) }}</pre>
        </div>
        <div v-if="store.detail.result" class="jobdet__sec">
          <div class="jobdet__lbl">{{ t.job_result }}</div>
          <pre class="jobdet__json mono">{{ prettyJson(store.detail.result) }}</pre>
        </div>
        <div v-if="store.detail.error" class="jobdet__sec">
          <div class="jobdet__lbl is-err">{{ t.job_error }}</div>
          <pre class="jobdet__json mono is-err">{{ store.detail.error }}</pre>
        </div>

        <div v-if="store.detail.status === 'needs_verification'" class="jobdet__verify">
          <Icon name="eye" :size="16" />
          <span>{{ t.s_needs_verification }}</span>
          <Btn size="sm" variant="primary" icon="check" @click="store.verify(store.detail.id)">
            {{ t.job_verify }}
          </Btn>
        </div>
      </div>
    </Sheet>
  </DataPage>
</template>
