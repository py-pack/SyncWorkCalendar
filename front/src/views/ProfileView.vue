<script setup lang="ts">
// Екран «Профіль» (frontend-profile): DataPage з двома закладками (in-view tab —
// один маршрут, без вкладених роутів). «Особисті дані» — self-edit username/
// worker_key (email/is_active read-only) + зміна пароля. «Синхронізації» —
// перемикачі sync_prefs (окремий компонент).
import { computed, reactive, ref, watch } from 'vue'

import { ApiError } from '@/api/types'
import type { TabItem } from '@/components/data/types'
import DataPage from '@/components/data/DataPage.vue'
import SyncPrefsToggles from '@/components/profile/SyncPrefsToggles.vue'
import Btn from '@/components/ui/Btn.vue'
import Field from '@/components/ui/Field.vue'
import { useI18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()

const tab = ref<'personal' | 'sync'>('personal')
const tabs = computed<TabItem[]>(() => [
  { id: 'personal', label: t.value.prof_tab_personal, icon: 'user' },
  { id: 'sync', label: t.value.prof_tab_sync, icon: 'sync' },
])

const me = computed(() => auth.currentUser)

// --- Особисті дані (self-edit) ---
const ident = reactive({ username: '', worker_key: '' })
watch(
  me,
  (u) => {
    ident.username = u?.username ?? ''
    ident.worker_key = u?.worker_key ?? ''
  },
  { immediate: true },
)

const savingIdent = ref(false)
const identErr = ref('')
const identOk = ref(false)
async function saveIdent(): Promise<void> {
  if (savingIdent.value || !ident.username.trim()) return
  savingIdent.value = true
  identErr.value = ''
  identOk.value = false
  try {
    await auth.updateMe({
      username: ident.username.trim(),
      worker_key: ident.worker_key.trim() || null,
    })
    identOk.value = true
  } catch (e) {
    identErr.value = e instanceof ApiError ? e.detail : String(e)
  } finally {
    savingIdent.value = false
  }
}

// --- Пароль (через хешування на беку) ---
const pw = reactive({ current: '', next: '' })
const savingPw = ref(false)
const pwErr = ref('')
const pwOk = ref(false)
async function savePw(): Promise<void> {
  if (savingPw.value || !pw.next) return
  savingPw.value = true
  pwErr.value = ''
  pwOk.value = false
  try {
    await auth.changeMyPassword({ current_password: pw.current || null, new_password: pw.next })
    pwOk.value = true
    pw.current = ''
    pw.next = ''
  } catch (e) {
    pwErr.value = e instanceof ApiError ? e.detail : String(e)
  } finally {
    savingPw.value = false
  }
}
</script>

<template>
  <DataPage
    :title="t.prof_title"
    :desc="t.prof_desc"
    :tabs="tabs"
    :active-tab="tab"
    @update:active-tab="tab = $event as 'personal' | 'sync'"
  >
    <template v-if="tab === 'personal'">
      <div class="prof">
        <section class="prof__sec">
          <h2 class="prof__h">{{ t.prof_identity }}</h2>
          <Field :label="t.user_full_name">
            <input v-model="ident.username" class="sw-input" placeholder="i.petrenko" />
          </Field>
          <Field :label="t.user_worker_key" hint="Jira key">
            <input v-model="ident.worker_key" class="sw-input mono" placeholder="i.petrenko" />
          </Field>
          <Field :label="t.col_email">
            <input class="sw-input" :value="me?.email ?? '—'" disabled />
          </Field>
          <Field :label="t.user_active">
            <input
              class="sw-input"
              :value="me?.is_active ? t.user_active : t.user_disabled"
              disabled
            />
          </Field>

          <p v-if="identErr" class="data-error">{{ identErr }}</p>
          <div class="prof__foot">
            <span v-if="identOk" class="prof__ok">{{ t.prof_saved }}</span>
            <Btn
              variant="primary"
              icon="check"
              :disabled="savingIdent || !ident.username.trim()"
              @click="saveIdent"
            >
              {{ t.prof_save }}
            </Btn>
          </div>
        </section>

        <section class="prof__sec">
          <h2 class="prof__h">{{ t.prof_pw_title }}</h2>
          <p class="prof__hint">{{ t.prof_pw_first_hint }}</p>
          <Field :label="t.prof_pw_current">
            <input v-model="pw.current" type="password" class="sw-input" autocomplete="current-password" />
          </Field>
          <Field :label="t.prof_pw_new">
            <input v-model="pw.next" type="password" class="sw-input" autocomplete="new-password" />
          </Field>

          <p v-if="pwErr" class="data-error">{{ pwErr }}</p>
          <div class="prof__foot">
            <span v-if="pwOk" class="prof__ok">{{ t.prof_pw_ok }}</span>
            <Btn variant="primary" icon="lock" :disabled="savingPw || !pw.next" @click="savePw">
              {{ t.prof_pw_change }}
            </Btn>
          </div>
        </section>
      </div>
    </template>

    <template v-else>
      <SyncPrefsToggles />
    </template>
  </DataPage>
</template>
