<script setup lang="ts">
import Badge from '@/components/ui/Badge.vue'
import Icon from '@/components/ui/Icon.vue'

import type { TabItem } from './types'

defineProps<{ tabs: TabItem[]; modelValue: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>

<template>
  <div class="page__tabs">
    <button
      v-for="tb in tabs"
      :key="tb.id"
      type="button"
      :class="['page__tab', { 'is-active': modelValue === tb.id }]"
      @click="emit('update:modelValue', tb.id)"
    >
      <Icon v-if="tb.icon" :name="tb.icon" :size="15" />
      {{ tb.label }}
      <Badge v-if="tb.count != null" tone="neutral" soft>{{ tb.count }}</Badge>
    </button>
  </div>
</template>
