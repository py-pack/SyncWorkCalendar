<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

import Icon from './Icon.vue'
import type { MenuItem } from './types'

const props = defineProps<{ items: MenuItem[] }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const root = ref<HTMLElement | null>(null)

function onPointerDown(e: Event): void {
  if (root.value && !root.value.contains(e.target as Node)) emit('close')
}
function onKey(e: KeyboardEvent): void {
  if (e.key === 'Escape') emit('close')
}
function pick(it: MenuItem): void {
  if (it.disabled) return
  it.onClick?.()
  emit('close')
}

onMounted(() => {
  document.addEventListener('mousedown', onPointerDown)
  document.addEventListener('touchstart', onPointerDown)
  document.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onPointerDown)
  document.removeEventListener('touchstart', onPointerDown)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <div ref="root" class="sw-menu" @click.stop>
    <template v-for="(it, i) in props.items" :key="i">
      <div v-if="it.divider" class="sw-menu__div" />
      <button
        v-else
        :class="['sw-menu__item', { 'is-danger': it.danger }]"
        :disabled="it.disabled"
        @click="pick(it)"
      >
        <Icon v-if="it.icon" :name="it.icon" :size="16" />
        <span>{{ it.label }}</span>
        <span v-if="it.hint" class="sw-menu__hint">{{ it.hint }}</span>
      </button>
    </template>
  </div>
</template>
