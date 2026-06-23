<script setup lang="ts">
// Єдиний індикатор стану синку для ВСІХ дані-екранів (timecamp / projects).
// Крапка + короткий підпис; візуально ІДЕНТИЧНИЙ скрізь — це суть продукту.
// Підпис англійською в обох локалях (свідомо: спільна «мова синку» застосунку,
// рішення користувача — коротко й однаково). Див. systemPatterns.md.
defineProps<{ synced: boolean }>()
</script>

<template>
  <span class="syncst" :class="{ 'is-on': synced }" :title="synced ? 'Synced' : 'Not synced'">
    <span class="syncst__dot" />
    {{ synced ? 'Synced' : 'Not synced' }}
  </span>
</template>
