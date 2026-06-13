/* =========================================================================
   Sync Work — стор користувачів (api-users-management). CRUD з локальним
   оновленням списку. create/toggle/remove кидають ApiError далі (форма/таблиця
   показують 409/інше); load ховає помилку в `error`.
   ========================================================================= */
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api } from '@/api/client'
import { ApiError, type UserCreate, type UserItem, type UserPatch } from '@/api/types'

function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.detail
  return e instanceof Error ? e.message : String(e)
}

export const useUsersStore = defineStore('users', () => {
  const users = ref<UserItem[]>([])
  const error = ref<string | null>(null)

  async function load(): Promise<void> {
    error.value = null
    try {
      users.value = await api.users()
    } catch (e) {
      error.value = errMsg(e)
    }
  }

  async function create(body: UserCreate): Promise<UserItem> {
    const created = await api.createUser(body)
    users.value = [...users.value, created]
    return created
  }

  async function update(id: number, body: UserPatch): Promise<UserItem> {
    const updated = await api.patchUser(id, body)
    users.value = users.value.map((x) => (x.id === updated.id ? updated : x))
    return updated
  }

  async function toggleActive(u: UserItem): Promise<void> {
    const updated = await api.patchUser(u.id, { is_active: !u.is_active })
    users.value = users.value.map((x) => (x.id === updated.id ? updated : x))
  }

  async function remove(u: UserItem): Promise<void> {
    await api.deleteUser(u.id)
    users.value = users.value.filter((x) => x.id !== u.id)
  }

  return { users, error, load, create, update, toggleActive, remove }
})
