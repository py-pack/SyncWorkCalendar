<script setup lang="ts">
import Icon from './Icon.vue'
import type { SegmentedOption } from './types'

withDefaults(
  defineProps<{
    modelValue: string
    options: SegmentedOption[]
    size?: 'sm' | 'md'
  }>(),
  { size: 'md' },
)

const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>

<template>
  <div :class="['sw-seg', `sw-seg--${size}`]">
    <button
      v-for="o in options"
      :key="o.value"
      type="button"
      :class="['sw-seg__opt', { 'is-active': modelValue === o.value }]"
      :title="o.title"
      @click="emit('update:modelValue', o.value)"
    >
      <Icon v-if="o.icon" :name="o.icon" :size="15" />
      <span v-if="o.label">{{ o.label }}</span>
    </button>
  </div>
</template>
