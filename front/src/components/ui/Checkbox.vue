<script setup lang="ts">
import { computed } from 'vue'

import Icon from './Icon.vue'

const props = defineProps<{
  checked: boolean
  indeterminate?: boolean
}>()

const emit = defineEmits<{ (e: 'update:checked', value: boolean): void }>()

const classes = computed(() => [
  'sw-check',
  { 'is-on': props.checked, 'is-ind': props.indeterminate },
])

function toggle(e: MouseEvent): void {
  e.stopPropagation()
  emit('update:checked', !props.checked)
}
</script>

<template>
  <span :class="classes" @click="toggle">
    <Icon v-if="checked && !indeterminate" name="check" :size="12" :stroke="2.4" />
    <span v-if="indeterminate" class="sw-check__dash" />
  </span>
</template>
