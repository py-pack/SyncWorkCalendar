<script setup lang="ts">
import { computed } from 'vue'

import Icon from './Icon.vue'

const props = withDefaults(
  defineProps<{
    variant?: 'default' | 'primary' | 'ghost' | 'soft' | 'danger'
    size?: 'sm' | 'md' | 'lg'
    icon?: string
    iconRight?: string
    disabled?: boolean
    active?: boolean
    full?: boolean
    title?: string
    type?: 'button' | 'submit'
  }>(),
  { variant: 'default', size: 'md', type: 'button' },
)

const classes = computed(() => [
  'sw-btn',
  `sw-btn--${props.variant}`,
  `sw-btn--${props.size}`,
  { 'is-active': props.active, 'is-full': props.full },
])
const iconSize = computed(() => (props.size === 'sm' ? 15 : 17))
</script>

<template>
  <button :type="type" :class="classes" :disabled="disabled" :title="title">
    <Icon v-if="icon" :name="icon" :size="iconSize" />
    <span v-if="$slots.default"><slot /></span>
    <Icon v-if="iconRight" :name="iconRight" :size="iconSize" />
  </button>
</template>
