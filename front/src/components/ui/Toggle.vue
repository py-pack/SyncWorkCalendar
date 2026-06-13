<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    checked: boolean
    size?: 'sm' | 'md'
  }>(),
  { size: 'md' },
)

const emit = defineEmits<{ (e: 'update:checked', value: boolean): void }>()

const classes = computed(() => ['sw-toggle', `sw-toggle--${props.size}`, { 'is-on': props.checked }])
</script>

<template>
  <button
    type="button"
    :class="classes"
    role="switch"
    :aria-checked="checked"
    @click="emit('update:checked', !checked)"
  >
    <span class="sw-toggle__knob" />
  </button>
</template>
