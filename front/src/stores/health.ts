// Базовий Pinia-store-каркас (приклад роботи store + API-клієнт).

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

export const useHealthStore = defineStore('health', () => {
  const status = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchHealth(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const res = await api.getHealth()
      status.value = res.status
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  return { status, loading, error, fetchHealth }
})
