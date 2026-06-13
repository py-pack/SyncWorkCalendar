<script setup lang="ts">
import { computed, onMounted } from 'vue'

import DataTable from '@/components/data/DataTable.vue'
import PageHeader from '@/components/data/PageHeader.vue'
import StatusBadge from '@/components/data/StatusBadge.vue'
import SyncBtn from '@/components/data/SyncBtn.vue'
import type { Column } from '@/components/data/types'
import Badge from '@/components/ui/Badge.vue'
import Btn from '@/components/ui/Btn.vue'
import Icon from '@/components/ui/Icon.vue'
import Sheet from '@/components/ui/Sheet.vue'
import Spinner from '@/components/ui/Spinner.vue'
import { useI18n } from '@/i18n'
import { useJournalStore } from '@/stores/journal'
import type { JournalFilter } from '@/stores/journal'

const { t } = useI18n()
const store = useJournalStore()

const filters = computed<{ id: JournalFilter; label: string }[]>(() => [
  { id: 'all', label: t.value.cal_all },
  { id: 'needs_verification', label: t.value.s_needs_verification },
  { id: 'failed', label: t.value.s_failed },
  { id: 'running', label: t.value.s_running },
])

const cols = computed<Column[]>(() => [
  { key: 'id', label: 'ID', width: 90, mono: true },
  { key: 'trigger_name', label: t.value.job_trigger },
  { key: 'status', label: t.value.col_status, width: 170 },
  { key: 'started_at', label: t.value.job_started, width: 160, mono: true },
  { key: 'created_by', label: t.value.job_by, width: 120, mono: true },
  { key: 'act', label: '', align: 'right', width: 130 },
])

function prettyJson(value: unknown): string {
  return JSON.stringify(value, null, 2)
}

onMounted(() => void store.load())
</script>

<template>
  <div class="page">
    <PageHeader :title="t.jr_journal_title" :desc="t.jr_journal_desc">
      <template #actions>
        <SyncBtn :label="t.tbl_refresh" icon="sync" :action="() => store.load()" />
      </template>
    </PageHeader>

    <div class="pipe">
      <div class="cal__chips">
        <button
          v-for="f in filters"
          :key="f.id"
          type="button"
          :class="['chip', { 'is-on': store.filter === f.id }]"
          @click="store.setFilter(f.id)"
        >
          {{ f.label }}
        </button>
      </div>
    </div>

    <p v-if="store.error" class="data-error"><Icon name="alert" :size="15" />{{ store.error }}</p>

    <div class="page__body">
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
        <template #cell-started_at="{ row }">{{ row.started_at.slice(5, 16) }}</template>
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
          <Icon v-else name="chevR" :size="16" />
        </template>
      </DataTable>
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
          <div><span class="muted">{{ t.job_started }}</span><span class="mono">{{ store.detail.started_at.slice(0, 19) }}</span></div>
          <div><span class="muted">{{ t.job_finished }}</span><span class="mono">{{ store.detail.finished_at ? store.detail.finished_at.slice(0, 19) : '—' }}</span></div>
          <div><span class="muted">{{ t.job_verified_by }}</span><span class="mono">{{ store.detail.verified_by || '—' }}</span></div>
          <div><span class="muted">verified_at</span><span class="mono">{{ store.detail.verified_at ? store.detail.verified_at.slice(11, 19) : '—' }}</span></div>
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
  </div>
</template>
