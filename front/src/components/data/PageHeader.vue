<script setup lang="ts">
// Заголовок дані-екрана: title + опис + слот дій (праворуч).
defineProps<{ title: string; desc?: string }>()
</script>

<template>
  <div class="page__head">
    <div class="page__titles">
      <h1>{{ title }}</h1>
      <p v-if="desc">{{ desc }}</p>
    </div>
    <div v-if="$slots.actions" class="page__actions"><slot name="actions" /></div>
  </div>
</template>
