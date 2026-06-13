<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import Icon from '@/components/ui/Icon.vue'
import { useI18n } from '@/i18n'
import type { StringKey } from '@/i18n/strings'

// Тимчасова заглушка для екранів, які реалізують фази 2–3
// (add-calendar-timesheet, add-data-screens). Заголовок — з i18n за meta.
const { t } = useI18n()
const route = useRoute()

const meta = computed(() => route.meta as { titleKey?: StringKey; icon?: string })
const title = computed(() => {
  const key = meta.value.titleKey
  return key ? t.value[key] : String(route.name ?? '')
})
const icon = computed(() => meta.value.icon ?? 'bolt')
</script>

<template>
  <div class="page">
    <div class="page__head">
      <div class="page__titles">
        <h1>{{ title }}</h1>
      </div>
    </div>
    <div class="page__body">
      <div class="page__empty">
        <Icon :name="icon" :size="34" :stroke="1.3" />
        <p>{{ t.coming_soon }}</p>
      </div>
    </div>
  </div>
</template>
