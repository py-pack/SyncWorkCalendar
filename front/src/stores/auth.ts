/* =========================================================================
   Sync Work — auth-store. Усі три способи входу (логін/пароль, Google
   credential/One Tap, Google code/popup) дають один наш JWT із бекенду.
   Токен персиститься через storage-обгортку (ключ auth.token) — та сама
   точка, звідки його читає api/client для Authorization-заголовка.
   ========================================================================= */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { api } from '@/api/client'
import type { CurrentUserResponse, GoogleAuthPayload } from '@/api/types'
import { useStored } from '@/lib/storage'

export const useAuthStore = defineStore('auth', () => {
  const token = useStored<string | null>('auth.token', null)
  const currentUser = ref<CurrentUserResponse | null>(null)

  const isAuthed = computed(() => !!token.value)

  async function fetchMe(): Promise<void> {
    currentUser.value = await api.me()
  }

  async function login(username: string, password: string): Promise<void> {
    const res = await api.login(username, password)
    token.value = res.access_token
    await fetchMe()
  }

  async function loginWithGoogle(payload: GoogleAuthPayload): Promise<void> {
    const res = await api.google(payload)
    token.value = res.access_token
    await fetchMe()
  }

  async function refresh(): Promise<void> {
    const res = await api.refresh()
    token.value = res.access_token
  }

  function logout(): void {
    token.value = null
    currentUser.value = null
  }

  return { token, currentUser, isAuthed, login, loginWithGoogle, refresh, fetchMe, logout }
})
