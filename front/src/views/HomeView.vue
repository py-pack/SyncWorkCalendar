<script setup lang="ts">
import { useHealthStore } from '../stores/health'

const health = useHealthStore()
</script>

<template>
  <main class="home">
    <h1>Sync Work Calendar</h1>
    <p>Каркас фронтенду (Vue 3 + Vite + TypeScript).</p>

    <button :disabled="health.loading" @click="health.fetchHealth()">
      Перевірити API
    </button>

    <p v-if="health.loading">Завантаження…</p>
    <p v-else-if="health.error" class="error">Помилка: {{ health.error }}</p>
    <p v-else-if="health.status">API статус: {{ health.status }}</p>
  </main>
</template>

<style scoped>
.home {
  max-width: 40rem;
  margin: 2rem auto;
  font-family: system-ui, sans-serif;
}
.error {
  color: #c0392b;
}
</style>
