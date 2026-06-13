<script setup lang="ts">
// Auth-gate: без валідної сесії показуємо екран входу замість оболонки,
// незалежно від запитаного маршруту (web-app-shell / web-auth).
import AppShell from '@/components/AppShell.vue'
import AuthView from '@/views/AuthView.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <AuthView v-if="!auth.isAuthed" />
  <AppShell v-else />
</template>
