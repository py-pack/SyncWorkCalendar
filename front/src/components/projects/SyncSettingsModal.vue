<script setup lang="ts">
// Попап налаштувань синку TimeCamp-проекту (rework-projects-screen, D7/D8).
// Тогл «увімкнути синк» + select задачі з пошуком (debounce → /jr-issues).
// Правило Save: коли синк увімкнено, але задачу не обрано — Save disabled.
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import type { JRIssue, TCProject } from '@/api/types'
import Btn from '@/components/ui/Btn.vue'
import IconBtn from '@/components/ui/IconBtn.vue'
import Sheet from '@/components/ui/Sheet.vue'
import Spinner from '@/components/ui/Spinner.vue'
import Toggle from '@/components/ui/Toggle.vue'
import { useI18n } from '@/i18n'
import { useTablesStore } from '@/stores/tables'

const props = defineProps<{ project: TCProject | null }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const { t } = useI18n()
const store = useTablesStore()

const open = computed(() => props.project !== null)

const enabled = ref(false)
const selKey = ref<string | null>(null)
const selName = ref<string | null>(null)
const selActive = ref<boolean | null>(null)
const query = ref('')
const results = ref<JRIssue[]>([])
const searching = ref(false)
const saving = ref(false)
const err = ref<string | null>(null)

// Ініціалізація при відкритті (зміна project). Назва вже-змапованої задачі
// береться з project.issue_name — без окремого запиту (D8).
watch(
  () => props.project,
  (p) => {
    if (!p) return
    enabled.value = p.is_sync
    selKey.value = p.issue_key
    selName.value = p.issue_name
    selActive.value = p.issue_active
    query.value = ''
    results.value = []
    err.value = null
  },
  { immediate: true },
)

let timer: ReturnType<typeof setTimeout> | undefined
watch(query, (q) => {
  if (timer) clearTimeout(timer)
  const text = q.trim()
  if (!text) {
    results.value = []
    searching.value = false
    return
  }
  searching.value = true
  timer = setTimeout(() => {
    void store
      .jrIssueSearch(text)
      .then((r) => {
        results.value = r
      })
      .catch(() => {
        results.value = []
      })
      .finally(() => {
        searching.value = false
      })
  }, 250)
})
onBeforeUnmount(() => {
  if (timer) clearTimeout(timer)
})

function pick(it: JRIssue): void {
  selKey.value = it.key
  selName.value = it.name
  selActive.value = it.active
  // Вибір задачі = намір синкати: вмикаємо синк, інакше Save відправив би
  // `is_sync:false` і мовчки відкинув `issue_key` (звʼязок не зберігся б).
  enabled.value = true
  query.value = ''
  results.value = []
}

function clearSel(): void {
  selKey.value = null
  selName.value = null
  selActive.value = null
}

// Save disabled, поки синк увімкнено, а задачу не обрано (D7).
const canSave = computed(() => !enabled.value || !!selKey.value)

async function save(): Promise<void> {
  if (!props.project || !canSave.value || saving.value) return
  saving.value = true
  err.value = null
  try {
    // Вимкнення синку → шлемо лише is_sync:false; наявний issue_key бек зберігає.
    const patch = enabled.value
      ? { is_sync: true, issue_key: selKey.value as string }
      : { is_sync: false }
    await store.saveTcSync(props.project.id, patch)
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
      <div class="ssm__proj">{{ project.name }}</div>

      <div class="ssm__row">
        <span class="ssm__rowlabel">{{ t.ssm_enable }}</span>
        <Toggle :checked="enabled" @update:checked="enabled = $event" />
      </div>

      <!-- НЕ обгортаємо клікабельний список у <label> (Field): клік по пункту
           перехоплює активація label → фокус на input. Той самий вигляд — div. -->
      <div class="sw-field">
        <span class="sw-field__label">{{ t.ssm_task }}</span>

        <div v-if="selKey" class="ssm__sel" :class="{ 'is-dim': selActive === false }">
          <span class="mono">{{ selKey }}</span>
          <span v-if="selName" class="ssm__selname">{{ selName }}</span>
          <IconBtn name="x" size="sm" @click="clearSel" />
        </div>

        <input v-model="query" class="sw-input" :placeholder="t.ssm_search" />

        <div v-if="searching" class="ssm__searching"><Spinner :size="14" /></div>
        <ul v-else-if="results.length" class="ssm__results">
          <li
            v-for="it in results"
            :key="it.id"
            class="ssm__opt"
            :class="{ 'is-dim': !it.active }"
            @click="pick(it)"
          >
            <span class="mono">{{ it.key }}</span>
            <span class="ssm__optname">{{ it.name }}</span>
          </li>
        </ul>
        <p v-else-if="query.trim()" class="ssm__nores">{{ t.ssm_no_results }}</p>

        <span class="sw-field__hint">{{ t.ssm_task_hint }}</span>
      </div>

      <p v-if="err" class="data-error">{{ err }}</p>

      <div class="ssm__foot">
        <Btn variant="default" :disabled="saving" @click="emit('close')">{{ t.blk_cancel }}</Btn>
        <Btn variant="primary" icon="check" :disabled="!canSave || saving" @click="save">
          <Spinner v-if="saving" :size="14" />
          <template v-else>{{ t.blk_save }}</template>
        </Btn>
      </div>
    </div>
  </Sheet>
</template>
