<script setup lang="ts"></script>

<template>
  <header class="app-header">
    <nav>
      <RouterLink to="/">Головна</RouterLink>
    </nav>
  </header>
  <RouterView />
</template>

<style scoped>
.app-header {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #ddd;
  font-family: system-ui, sans-serif;
}
</style>
