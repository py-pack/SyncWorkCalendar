<script setup lang="ts">
// Єдиний фільтр стану синку для ВСІХ дані-екранів (timecamp / projects).
// Сегментований контрол; візуально ІДЕНТИЧНИЙ скрізь. Підписи англійською в
// обох локалях (свідомо: спільна «мова синку», рішення користувача).
// Канонічний tri-стан `SyncTri`. Див. systemPatterns.md.
import type { SyncTri } from '@/api/types'
import Segmented from '@/components/ui/Segmented.vue'
import type { SegmentedOption } from '@/components/ui/types'

defineProps<{ modelValue: SyncTri }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: SyncTri): void }>()

const OPTIONS: SegmentedOption[] = [
  { value: 'all', label: 'All' },
  { value: 'synced', label: 'Synced' },
  { value: 'unsynced', label: 'Not synced' },
]
</script>

<template>
  <Segmented
    :model-value="modelValue"
    :options="OPTIONS"
    size="sm"
    @update:model-value="emit('update:modelValue', $event as SyncTri)"
  />
</template>
