<script setup lang="ts">
import { computed } from 'vue'

import IconBtn from './IconBtn.vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title?: string
    width?: number
    side?: 'right' | 'left'
  }>(),
  { width: 380, side: 'right' },
)

const emit = defineEmits<{ (e: 'close'): void }>()

const panelStyle = computed(() => ({ width: `${props.width}px` }))
</script>

<template>
  <div v-if="open" class="sw-sheet-overlay" @mousedown="emit('close')">
    <div :class="['sw-sheet', `sw-sheet--${side}`]" :style="panelStyle" @mousedown.stop>
      <div v-if="title" class="sw-sheet__head">
        <div class="sw-sheet__title">{{ title }}</div>
        <IconBtn name="x" size="sm" @click="emit('close')" />
      </div>
      <div class="sw-sheet__body"><slot /></div>
    </div>
  </div>
</template>
