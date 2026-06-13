<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'

import Btn from '@/components/ui/Btn.vue'
import Spinner from '@/components/ui/Spinner.vue'

// Кнопка sync-тригера зі станами idle → running → done (D5). `action` —
// реальний виклик API; на успіх показуємо «done» ~1.6 с і повертаємось у idle.
const props = withDefaults(
  defineProps<{
    label: string
    icon?: string
    variant?: 'default' | 'primary' | 'ghost' | 'soft' | 'danger'
    size?: 'sm' | 'md' | 'lg'
    action?: () => Promise<unknown>
  }>(),
  { icon: 'sync', variant: 'default', size: 'sm' },
)

const emit = defineEmits<{
  (e: 'done'): void
  (e: 'error', err: unknown): void
}>()

type State = 'idle' | 'running' | 'done'
const state = ref<State>('idle')
let resetTimer: ReturnType<typeof setTimeout> | undefined

async function run(): Promise<void> {
  if (state.value === 'running') return
  state.value = 'running'
  try {
    if (props.action) await props.action()
    state.value = 'done'
    emit('done')
    resetTimer = setTimeout(() => {
      state.value = 'idle'
    }, 1600)
  } catch (e) {
    state.value = 'idle'
    emit('error', e)
  }
}

onBeforeUnmount(() => {
  if (resetTimer) clearTimeout(resetTimer)
})
</script>

<template>
  <Btn
    :size="size"
    :variant="state === 'done' ? 'soft' : variant"
    :icon="state === 'running' ? undefined : state === 'done' ? 'check' : icon"
    :disabled="state === 'running'"
    @click="run"
  >
    <Spinner v-if="state === 'running'" :size="14" />
    <template v-else>{{ label }}</template>
  </Btn>
</template>
