<script setup lang="ts">
import { computed } from 'vue'

import { ICONS } from '@/lib/icons'

const props = withDefaults(
  defineProps<{
    name: string
    size?: number
    stroke?: number
    fill?: boolean
  }>(),
  { size: 18, stroke: 1.6, fill: false },
)

const path = computed(() => ICONS[props.name] ?? '')
</script>

<template>
  <!-- Google — особлива багатоколірна іконка -->
  <svg v-if="name === 'google'" :width="size" :height="size" viewBox="0 0 24 24">
    <path fill="#4285F4" d="M22 12.2c0-.7-.1-1.4-.2-2H12v3.8h5.6a4.8 4.8 0 0 1-2.1 3.2v2.6h3.4c2-1.8 3.1-4.5 3.1-7.6Z" />
    <path fill="#34A853" d="M12 22c2.7 0 5-.9 6.7-2.4l-3.4-2.6c-.9.6-2.1 1-3.3 1-2.6 0-4.7-1.7-5.5-4.1H3v2.6A10 10 0 0 0 12 22Z" />
    <path fill="#FBBC05" d="M6.5 13.9a6 6 0 0 1 0-3.8V7.5H3a10 10 0 0 0 0 9l3.5-2.6Z" />
    <path fill="#EA4335" d="M12 6.1c1.5 0 2.8.5 3.8 1.5l2.9-2.9A10 10 0 0 0 3 7.5l3.5 2.6C7.3 7.8 9.4 6.1 12 6.1Z" />
  </svg>
  <svg
    v-else
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    :fill="fill ? 'currentColor' : 'none'"
    stroke="currentColor"
    :stroke-width="stroke"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <path :d="path" />
  </svg>
</template>
