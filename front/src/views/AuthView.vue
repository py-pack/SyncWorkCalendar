<script setup lang="ts">
import { onMounted, ref } from 'vue'

import BrandMark from '@/components/BrandMark.vue'
import Btn from '@/components/ui/Btn.vue'
import Checkbox from '@/components/ui/Checkbox.vue'
import Field from '@/components/ui/Field.vue'
import Icon from '@/components/ui/Icon.vue'
import IconBtn from '@/components/ui/IconBtn.vue'
import Segmented from '@/components/ui/Segmented.vue'
import Spinner from '@/components/ui/Spinner.vue'
import { ApiError, type GoogleAuthPayload } from '@/api/types'
import { useI18n } from '@/i18n'
import type { Lang } from '@/i18n/strings'
import { googleEnabled, initOneTap, requestGoogleCode } from '@/lib/google'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const { t, lang, setLang } = useI18n()
const ui = useUiStore()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const remember = ref(true)
const loading = ref<null | 'pass' | 'google'>(null)
const error = ref('')

async function submitPassword(): Promise<void> {
  if (loading.value) return
  loading.value = 'pass'
  error.value = ''
  try {
    // Поле «Логін або e-mail» → username наявного /auth/login.
    await auth.login(email.value, password.value)
    // Успіх: App.vue реактивно покаже оболонку (auth-gate).
  } catch (e) {
    error.value = e instanceof ApiError ? t.value.auth_error : String(e)
    loading.value = null
  }
}

async function doGoogle(payload: GoogleAuthPayload): Promise<void> {
  loading.value = 'google'
  error.value = ''
  try {
    await auth.loginWithGoogle(payload)
  } catch (e) {
    if (e instanceof ApiError) {
      error.value = e.status === 503 ? t.value.auth_google_off : t.value.auth_google_error
    } else {
      error.value = String(e)
    }
    loading.value = null
  }
}

function onGoogleClick(): void {
  if (loading.value) return
  if (!googleEnabled) {
    error.value = t.value.auth_google_off
    return
  }
  // popup auth-code флоу → {code}
  void requestGoogleCode((code) => void doGoogle({ code }))
}

onMounted(() => {
  // One Tap → {credential}; тихо ні-чого, якщо Google не налаштовано.
  void initOneTap((credential) => void doGoogle({ credential }))
})
</script>

<template>
  <div class="auth">
    <div class="auth__bg" aria-hidden="true">
      <div class="auth__grid" />
    </div>

    <div class="auth__topbar">
      <div class="auth__brand">
        <BrandMark :size="22" />
        <span>Sync Work</span>
      </div>
      <div class="row" style="gap: 8px">
        <Segmented
          size="sm"
          :model-value="lang"
          :options="[
            { value: 'uk', label: 'УКР' },
            { value: 'en', label: 'ENG' },
          ]"
          @update:model-value="(v: string) => setLang(v as Lang)"
        />
        <IconBtn
          variant="outline"
          :name="ui.theme === 'dark' ? 'sun' : 'moon'"
          @click="ui.toggleTheme()"
        />
      </div>
    </div>

    <div class="auth__card-wrap">
      <div class="auth__card">
        <div class="auth__head">
          <BrandMark :size="34" />
          <h1>{{ t.app_name }}</h1>
          <p class="auth__sub">{{ t.auth_subtitle }}</p>
          <div class="auth__tag mono">{{ t.auth_tagline }}</div>
        </div>

        <form class="auth__form" @submit.prevent="submitPassword">
          <Field :label="t.auth_email">
            <input
              v-model="email"
              class="sw-input"
              autocomplete="username"
              placeholder="name@leadsdoit.io"
            />
          </Field>
          <Field :label="t.auth_password">
            <input
              v-model="password"
              class="sw-input"
              type="password"
              autocomplete="current-password"
              placeholder="••••••••"
            />
          </Field>
          <div class="auth__row">
            <label class="auth__remember">
              <Checkbox v-model:checked="remember" />
              <span>{{ t.auth_remember }}</span>
            </label>
            <a class="auth__link" href="#" @click.prevent>{{ t.auth_forgot }}</a>
          </div>
          <p v-if="error" class="auth__error">{{ error }}</p>
          <Btn variant="primary" size="lg" full type="submit" :disabled="!!loading">
            <Spinner v-if="loading === 'pass'" :size="17" />
            <template v-else>{{ t.auth_signin }}</template>
          </Btn>
        </form>

        <div class="auth__or"><span>{{ t.auth_or }}</span></div>

        <button class="auth__google" :disabled="!!loading" @click="onGoogleClick">
          <Spinner v-if="loading === 'google'" :size="17" />
          <Icon v-else name="google" :size="18" />
          <span>{{ t.auth_google }}</span>
        </button>

        <div class="auth__note">
          <Icon name="lock" :size="13" />
          <span>{{ t.auth_no_signup }}</span>
        </div>
      </div>
      <div class="auth__hint mono">{{ t.auth_hint }}</div>
    </div>
  </div>
</template>
