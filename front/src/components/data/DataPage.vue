<script setup lang="ts">
// Переюзовний каркас сторінки для всіх дані-/табличних екранів
// (add-page-shell-template). Інкапсулює: .page-обгортку, заголовок (title +
// опц. desc) + дії у верхньому правому куті (#actions), опційні закладки
// (окремі під-сторінки: tabs + activeTab + update:activeTab — router-agnostic,
// навігацію робить в'юха), опційний суб-бар (#toolbar), авто-банер помилки
// (prop error) і тіло в .page__body (default-слот).
// Порядок: заголовок → закладки → тулбар → банер помилки → тіло.
import Tabs from '@/components/data/Tabs.vue'
import type { TabItem } from '@/components/data/types'
import Icon from '@/components/ui/Icon.vue'

withDefaults(
  defineProps<{
    title: string
    desc?: string
    error?: string | null
    tabs?: TabItem[]
    activeTab?: string
  }>(),
  { error: null },
)

const emit = defineEmits<{ (e: 'update:activeTab', id: string): void }>()
</script>

<template>
  <div class="page">
    <div class="page__head">
      <div class="page__titles">
        <h1>{{ title }}</h1>
        <p v-if="desc">{{ desc }}</p>
      </div>
      <div v-if="$slots.actions" class="page__actions"><slot name="actions" /></div>
    </div>

    <Tabs
      v-if="tabs && tabs.length"
      :model-value="activeTab ?? ''"
      :tabs="tabs"
      @update:model-value="emit('update:activeTab', $event)"
    />

    <slot name="toolbar" />

    <p v-if="error" class="data-error"><Icon name="alert" :size="15" />{{ error }}</p>

    <div class="page__body"><slot /></div>
  </div>
</template>
