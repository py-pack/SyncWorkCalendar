<script setup lang="ts">
import { computed } from 'vue'

import Icon from './Icon.vue'

const props = withDefaults(
  defineProps<{
    name: string
    title?: string
    active?: boolean
    size?: 'sm' | 'md'
    variant?: 'ghost' | 'outline'
    badge?: number | null
  }>(),
  { size: 'md', variant: 'ghost', badge: null },
)

const classes = computed(() => [
  'sw-iconbtn',
  `sw-iconbtn--${props.variant}`,
  `sw-iconbtn--${props.size}`,
  { 'is-active': props.active },
])
const iconSize = computed(() => (props.size === 'sm' ? 16 : 18))
</script>

<template>
  <button type="button" :class="classes" :title="title">
    <Icon :name="name" :size="iconSize" />
    <span v-if="badge != null" class="sw-iconbtn__badge">{{ badge }}</span>
  </button>
</template>
