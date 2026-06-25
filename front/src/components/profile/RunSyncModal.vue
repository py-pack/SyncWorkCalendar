<script setup lang="ts">
// Спільний попап «Запустити зараз» (add-profile-run-now-sync, D1/D2/D4). За
// зразком SyncEntriesModal: Sheet + PeriodPicker + спінер. Параметризований
// ключем дії (`RUN_ACTIONS`). Дві гілки результату: синхронні дії показують
// дельту, реконсиляція (`auto_linking`, відповідь `202 queued`) — повідомлення
// «у черзі — див. Журнал». Помилки (зокрема `400` без worker_key) — у попапі.
import { computed, ref, watch } from 'vue'

import { ApiError, type Period, type SyncPrefs } from '@/api/types'
import PeriodPicker from '@/components/data/PeriodPicker.vue'
import { RUN_ACTIONS } from '@/components/profile/runActions'
import Btn from '@/components/ui/Btn.vue'
import Field from '@/components/ui/Field.vue'
import Sheet from '@/components/ui/Sheet.vue'
import Spinner from '@/components/ui/Spinner.vue'
import { useI18n } from '@/i18n'
import { syncPeriod } from '@/lib/period'

const props = defineProps<{ open: boolean; actionKey: keyof SyncPrefs | null }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const { t } = useI18n()

const action = computed(() => (props.actionKey ? RUN_ACTIONS[props.actionKey] : null))

const period = ref<Period>(syncPeriod())
const syncing = ref(false)
const err = ref<string | null>(null)
// Стан результату: `null` — ще не запускали (показуємо picker); інакше — фінал.
const done = ref<'delta' | 'queued' | null>(null)
const delta = ref<[string, string][]>([]) // пари [ключ, значення] з `result`

// Скид стану на кожне відкриття/зміну дії — дефолт «цей місяць» (вузьке вікно).
watch(
  [() => props.open, () => props.actionKey],
  ([o]) => {
    if (!o) return
    period.value = syncPeriod()
    err.value = null
    syncing.value = false
    done.value = null
    delta.value = []
  },
  { immediate: true },
)

/** Перетворити `result` тригера на пари рядків для показу дельти. */
function toDelta(result: Record<string, unknown> | null): [string, string][] {
  if (!result) return []
  return Object.entries(result)
    .filter(([, v]) => v !== null && (typeof v === 'number' || typeof v === 'string' || typeof v === 'boolean'))
    .map(([k, v]) => [k, String(v)])
}

async function run(): Promise<void> {
  const act = action.value
  if (!act || syncing.value || !period.value.start || !period.value.end) return
  syncing.value = true
  err.value = null
  try {
    const res = await act.run(period.value)
    if (res.status === 'queued') {
      done.value = 'queued' // реконсиляція — лише enqueue (D2)
    } else {
      delta.value = toDelta(res.result)
      done.value = 'delta'
    }
  } catch (e) {
    err.value = e instanceof ApiError ? e.detail : e instanceof Error ? e.message : String(e)
  } finally {
    syncing.value = false
  }
}
</script>

<template>
  <Sheet
    :open="open"
    :title="action ? t[action.titleKey] : ''"
    :width="380"
    @close="emit('close')"
  >
    <div v-if="action" class="tcsync">
      <p class="tcsync__hint">{{ t[action.hintKey] }}</p>

      <!-- Гілка результату (D1/D2): дельта або «у черзі». -->
      <template v-if="done">
        <p v-if="done === 'queued'" class="rsync__msg">{{ t.rsync_queued }}</p>
        <template v-else>
          <p class="rsync__msg">{{ t.rsync_done }}</p>
          <ul v-if="delta.length" class="rsync__delta">
            <li v-for="[k, v] in delta" :key="k">
              <span class="rsync__dk">{{ k }}</span>
              <span class="rsync__dv">{{ v }}</span>
            </li>
          </ul>
        </template>

        <div class="tcsync__foot">
          <Btn variant="primary" icon="check" @click="emit('close')">{{ t.rsync_close }}</Btn>
        </div>
      </template>

      <!-- Вибір періоду + запуск. -->
      <template v-else>
        <Field :label="t.tcsync_period">
          <PeriodPicker :model-value="period" @update:model-value="period = $event" />
        </Field>

        <p v-if="err" class="data-error">{{ err }}</p>

        <div class="tcsync__foot">
          <Btn variant="default" :disabled="syncing" @click="emit('close')">{{ t.blk_cancel }}</Btn>
          <Btn
            variant="primary"
            :icon="action.icon"
            :disabled="syncing || !period.start || !period.end"
            @click="run"
          >
            <Spinner v-if="syncing" :size="14" />
            <template v-else>{{ t.rsync_run }}</template>
          </Btn>
        </div>
      </template>
    </div>
  </Sheet>
</template>
