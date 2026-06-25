<script setup lang="ts">
// Закладка «Синхронізації» (frontend-profile): тумблер на кожен ключ sync_prefs.
// Дефолт — усе вимкнено (автосинк opt-in); зміна — оптимістична через auth-store
// (PATCH /users/me/sync-prefs) із відкатом на помилку. Підписи — двомовні (i18n),
// це налаштування, а не стан синку, тож «мова синку» тут не застосовується.
import { computed, ref } from 'vue'

import { ApiError, type SyncPrefs } from '@/api/types'
import Toggle from '@/components/ui/Toggle.vue'
import { useI18n } from '@/i18n'
import type { StringKey } from '@/i18n/strings'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()

const ROWS: { key: keyof SyncPrefs; label: StringKey; hint: StringKey }[] = [
  { key: 'auto_timecamp_pull', label: 'sp_timecamp', hint: 'sp_timecamp_hint' },
  { key: 'auto_jira_pull', label: 'sp_jira', hint: 'sp_jira_hint' },
  { key: 'auto_tempo_pull', label: 'sp_tempo', hint: 'sp_tempo_hint' },
  { key: 'auto_linking', label: 'sp_linking', hint: 'sp_linking_hint' },
  { key: 'auto_push_tempo', label: 'sp_push', hint: 'sp_push_hint' },
]

const prefs = computed(() => auth.currentUser?.sync_prefs)
const err = ref('')

async function toggle(key: keyof SyncPrefs, value: boolean): Promise<void> {
  err.value = ''
  try {
    await auth.setSyncPref(key, value)
  } catch (e) {
    err.value = e instanceof ApiError ? e.detail : String(e)
  }
}
</script>

<template>
  <div class="prof">
    <p class="prof__hint">{{ t.prof_sync_hint }}</p>
    <p v-if="err" class="data-error">{{ err }}</p>

    <div class="sprefs">
      <label v-for="row in ROWS" :key="row.key" class="sprefs__row">
        <span class="sprefs__txt">
          <span class="sprefs__label">{{ t[row.label] }}</span>
          <span class="sprefs__hint">{{ t[row.hint] }}</span>
        </span>
        <Toggle
          :checked="prefs?.[row.key] ?? false"
          @update:checked="toggle(row.key, $event)"
        />
      </label>
    </div>
  </div>
</template>
