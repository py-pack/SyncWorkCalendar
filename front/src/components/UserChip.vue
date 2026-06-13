<script setup lang="ts">
import { computed, ref } from 'vue'

import Avatar from '@/components/ui/Avatar.vue'
import Icon from '@/components/ui/Icon.vue'
import Menu from '@/components/ui/Menu.vue'
import type { MenuItem } from '@/components/ui/types'
import { useI18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

defineProps<{ collapsed?: boolean }>()

const { t } = useI18n()
const auth = useAuthStore()
const open = ref(false)

const name = computed(() => auth.currentUser?.username ?? '—')
const workerKey = computed(() => auth.currentUser?.worker_key ?? '')

// Ініціали з username (напр. "i.petrenko" → "IP").
const initials = computed(() => {
  const parts = name.value.split(/[^a-zA-Zа-яА-ЯіІїЇєЄ]+/).filter(Boolean)
  const letters = parts.length >= 2 ? parts[0][0] + parts[1][0] : name.value.slice(0, 2)
  return letters.toUpperCase()
})

// Стабільний відтінок avatar із username.
const hue = computed(() => {
  let h = 0
  for (const ch of name.value) h = (h * 31 + ch.charCodeAt(0)) % 360
  return h
})

const menuItems = computed<MenuItem[]>(() => [
  { label: t.value.profile, icon: 'user' },
  { label: t.value.settings, icon: 'settings' },
  { divider: true },
  { label: t.value.logout, icon: 'logout', danger: true, onClick: () => auth.logout() },
])
</script>

<template>
  <div class="userchip">
    <button class="userchip__btn" @click="open = !open">
      <Avatar :initials="initials" :hue="hue" :size="30" />
      <span v-if="!collapsed" class="userchip__info">
        <span class="userchip__name">{{ name }}</span>
        <span v-if="workerKey" class="userchip__key mono">{{ workerKey }}</span>
      </span>
      <Icon v-if="!collapsed" name="chevUp" :size="14" />
    </button>
    <Menu v-if="open" :items="menuItems" @close="open = false" />
  </div>
</template>
