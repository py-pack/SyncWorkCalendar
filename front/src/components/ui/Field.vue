<script setup lang="ts">
defineProps<{
  label?: string
  hint?: string
}>()
</script>

<template>
  <label class="sw-field">
    <span v-if="label" class="sw-field__label">{{ label }}</span>
    <slot />
    <span v-if="hint" class="sw-field__hint">{{ hint }}</span>
  </label>
</template>
