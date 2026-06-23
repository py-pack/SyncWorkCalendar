<script setup lang="ts">
// Попап синку записів TimeCamp (rework-timecamp-entries-screen, D1/D6/D8/D9).
// Компактний PeriodPicker (шаблони всередині) → POST /sync/timecamp/entries.
// Синк — лише явною дією звідси; екран сам ніколи не синкає (D1).
import { ref, watch } from 'vue'

import type { Period } from '@/api/types'
import PeriodPicker from '@/components/data/PeriodPicker.vue'
import Btn from '@/components/ui/Btn.vue'
import Field from '@/components/ui/Field.vue'
import Sheet from '@/components/ui/Sheet.vue'
import Spinner from '@/components/ui/Spinner.vue'
import { useI18n } from '@/i18n'
import { syncPeriod } from '@/lib/period'
import { useTablesStore } from '@/stores/tables'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const { t } = useI18n()
const store = useTablesStore()

const period = ref<Period>(syncPeriod())
const syncing = ref(false)
const err = ref<string | null>(null)

// При відкритті — дефолт «поточний місяць» (вузьке вікно синку), скидаємо стан.
watch(
  () => props.open,
  (o) => {
    if (!o) return
    period.value = syncPeriod()
    err.value = null
    syncing.value = false
  },
  { immediate: true },
)

async function run(): Promise<void> {
  if (syncing.value || !period.value.start || !period.value.end) return
  syncing.value = true
  err.value = null
  try {
    await store.syncTcEntries(period.value)
    emit('close')
  } catch (e) {
    err.value = e instanceof Error ? e.message : String(e)
  } finally {
    syncing.value = false
  }
}
</script>

<template>
  <Sheet :open="open" :title="t.tcsync_title" :width="380" @close="emit('close')">
    <div class="tcsync">
      <p class="tcsync__hint">{{ t.tcsync_hint }}</p>

      <Field :label="t.tcsync_period">
        <PeriodPicker :model-value="period" @update:model-value="period = $event" />
      </Field>

      <p v-if="err" class="data-error">{{ err }}</p>

      <div class="tcsync__foot">
        <Btn variant="default" :disabled="syncing" @click="emit('close')">{{ t.blk_cancel }}</Btn>
        <Btn
          variant="primary"
          icon="sync"
          :disabled="syncing || !period.start || !period.end"
          @click="run"
        >
          <Spinner v-if="syncing" :size="14" />
          <template v-else>{{ t.tcsync_run }}</template>
        </Btn>
      </div>
    </div>
  </Sheet>
</template>
