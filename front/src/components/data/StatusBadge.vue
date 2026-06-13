<script setup lang="ts">
import { computed } from 'vue'

import Badge from '@/components/ui/Badge.vue'
import { useI18n } from '@/i18n'

// Спільний бейдж для worklog-sync-task і api-job статусів (мапа з прототипу).
const props = defineProps<{ status: string }>()
const { t } = useI18n()

type Tone = 'neutral' | 'green' | 'amber' | 'red' | 'accent'
interface Meta {
  tone: Tone
  soft?: boolean
  icon?: string
}

const META: Record<string, Meta> = {
  pre_create: { tone: 'neutral', soft: true, icon: 'cloudDown' },
  create: { tone: 'accent', icon: 'clock' },
  created: { tone: 'green', icon: 'check' },
  pre_update: { tone: 'neutral', soft: true, icon: 'cloudDown' },
  update: { tone: 'accent', icon: 'clock' },
  updated: { tone: 'green', icon: 'check' },
  sync: { tone: 'accent', icon: 'sync' },
  failed: { tone: 'red', icon: 'alert' },
  running: { tone: 'accent', icon: 'sync' },
  needs_verification: { tone: 'amber', icon: 'eye' },
  verified: { tone: 'green', icon: 'check' },
}

const meta = computed<Meta>(() => META[props.status] ?? { tone: 'neutral' })
const label = computed<string>(() => {
  const dict = t.value as Record<string, string>
  return dict[`s_${props.status}`] ?? props.status
})
</script>

<template>
  <Badge :tone="meta.tone" :soft="meta.soft" :icon="meta.icon">{{ label }}</Badge>
</template>
