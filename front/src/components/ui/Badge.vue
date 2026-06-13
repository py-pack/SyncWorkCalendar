<script setup lang="ts">
import { computed } from 'vue'

import Icon from './Icon.vue'

const props = withDefaults(
  defineProps<{
    tone?: 'neutral' | 'green' | 'amber' | 'red' | 'accent'
    dot?: boolean
    soft?: boolean
    icon?: string
  }>(),
  { tone: 'neutral' },
)

const classes = computed(() => ['sw-badge', `sw-badge--${props.tone}`, { 'is-soft': props.soft }])
</script>

<template>
  <span :class="classes">
    <span v-if="dot" class="sw-badge__dot" />
    <Icon v-if="icon" :name="icon" :size="12" />
    <slot />
  </span>
</template>
