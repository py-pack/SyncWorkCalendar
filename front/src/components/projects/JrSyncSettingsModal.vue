<script setup lang="ts">
// Попап налаштувань синку Jira-проекту (rework-jira-projects-subview, D3).
// Простіший за TimeCamp-попап: ЛИШЕ тогл «увімкнути/вимкнути синхронізацію»
// (is_watched), без select-а задачі — Jira-проект не мапиться на одну задачу.
// Save ЗАВЖДИ дозволено (єдине поле — булевий тогл).
import { computed, ref, watch } from 'vue'

import type { JRProject } from '@/api/types'
import Btn from '@/components/ui/Btn.vue'
import Sheet from '@/components/ui/Sheet.vue'
import Spinner from '@/components/ui/Spinner.vue'
import Toggle from '@/components/ui/Toggle.vue'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'

const props = defineProps<{ project: JRProject | null }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const { t } = useI18n()
const store = useTablesStore()

const open = computed(() => props.project !== null)
const enabled = ref(false)
const saving = ref(false)
const err = ref<string | null>(null)

watch(
  () => props.project,
  (p) => {
    if (!p) return
    enabled.value = p.is_watched
    err.value = null
  },
  { immediate: true },
)

async function save(): Promise<void> {
  if (!props.project || saving.value) return
  saving.value = true
  err.value = null
  try {
    await store.saveJrWatched(props.project.id, enabled.value)
    emit('close')
  } catch (e) {
    err.value = e instanceof Error ? e.message : String(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Sheet :open="open" :title="t.ssm_title" :width="400" @close="emit('close')">
    <div v-if="project" class="ssm">
      <div class="ssm__proj"><span class="mono">{{ project.key }}</span> {{ project.name }}</div>

      <div class="ssm__row">
        <span class="ssm__rowlabel">{{ t.ssm_enable }}</span>
        <Toggle :checked="enabled" @update:checked="enabled = $event" />
      </div>

      <p v-if="err" class="data-error">{{ err }}</p>

      <div class="ssm__foot">
        <Btn variant="default" :disabled="saving" @click="emit('close')">{{ t.blk_cancel }}</Btn>
        <!-- Save завжди дозволено (лише тогл) -->
        <Btn variant="primary" icon="check" :disabled="saving" @click="save">
          <Spinner v-if="saving" :size="14" />
          <template v-else>{{ t.blk_save }}</template>
        </Btn>
      </div>
    </div>
  </Sheet>
</template>
