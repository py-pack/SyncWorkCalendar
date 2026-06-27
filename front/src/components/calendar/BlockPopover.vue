<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import Badge from '@/components/ui/Badge.vue'
import Btn from '@/components/ui/Btn.vue'
import Icon from '@/components/ui/Icon.vue'
import IconBtn from '@/components/ui/IconBtn.vue'
import { useI18n } from '@/i18n'
import type { CalendarBlock } from '@/api/types'
import { fmtSpan, hueForProject, splitLocal, syncMeta } from '@/lib/calendar'
import { fmtDur } from '@/lib/format'
import { projectColors } from '@/styles/palette'

const props = defineProps<{
  block: CalendarBlock
  anchor: { x: number; y: number }
  dark?: boolean
}>()
const emit = defineEmits<{ (e: 'close'): void }>()

const { t, lang } = useI18n()
const root = ref<HTMLElement | null>(null)

const colors = computed(() => projectColors(hueForProject(props.block.project)))
const meta = computed(() => syncMeta(props.block.status))

const span = computed(() => {
  const s = splitLocal(props.block.start)
  const e = splitLocal(props.block.end)
  const sameDay = e.date === s.date
  return { start: s.minutes, end: sameDay ? e.minutes : 24 * 60 }
})
const durMin = computed(() =>
  Math.max(1, Math.round((new Date(props.block.end).getTime() - new Date(props.block.start).getTime()) / 60000)),
)
const dateLabel = computed(() => {
  const locale = lang.value === 'uk' ? 'uk-UA' : 'en-US'
  return new Intl.DateTimeFormat(locale, { weekday: 'short', day: 'numeric', month: 'long' }).format(
    new Date(props.block.start),
  )
})

// Позиціонування біля курсора з утриманням у вікні (порт із прототипу).
const W = 320
const H = 300
const pos = computed(() => {
  let left = props.anchor.x + 14
  let top = props.anchor.y - 20
  if (left + W > window.innerWidth - 12) left = props.anchor.x - W - 14
  if (left < 12) left = 12
  if (top + H > window.innerHeight - 12) top = window.innerHeight - H - 12
  if (top < 12) top = 12
  return { left: `${left}px`, top: `${top}px`, width: `${W}px` }
})

function onKey(e: KeyboardEvent): void {
  if (e.key === 'Escape') emit('close')
}
function onDocDown(e: MouseEvent): void {
  if (root.value && !root.value.contains(e.target as Node)) emit('close')
}

onMounted(() => {
  document.addEventListener('keydown', onKey)
  document.addEventListener('mousedown', onDocDown)
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKey)
  document.removeEventListener('mousedown', onDocDown)
})
</script>

<template>
  <div ref="root" class="pop" :style="pos">
    <div class="pop__head" :style="{ background: dark ? colors.softDark : colors.soft }">
      <span class="pop__swatch" :style="{ background: colors.base }" />
      <span class="pop__proj">
        {{ block.project.name || t.cal_no_project }}
        <span v-if="block.project.key" class="muted"> · {{ block.project.key }}</span>
      </span>
      <span class="spacer" />
      <IconBtn name="x" size="sm" :title="t.blk_cancel" @click="emit('close')" />
    </div>

    <div class="pop__body">
      <div class="pop__when">
        <span class="pop__date">{{ dateLabel }}</span>
        <span class="pop__times mono">{{ fmtSpan(span.start, span.end) }}</span>
        <span class="pop__durpill mono">{{ fmtDur(durMin) }}</span>
      </div>

      <div class="pop__field">
        <span class="muted">{{ t.blk_issue }}</span>
        <span class="mono pop__val">{{ block.issue_key || '—' }}</span>
      </div>
      <div class="pop__field">
        <span class="muted">{{ t.blk_desc }}</span>
        <span class="pop__val">{{ block.description || '—' }}</span>
      </div>

      <div class="pop__r">
        <span class="muted">{{ t.col_status }}</span>
        <Badge :tone="meta.tone" soft :icon="meta.icon">{{ t[meta.labelKey] }}</Badge>
      </div>

      <p v-if="block.duplicate" class="pop__dup">
        <Icon name="alert" :size="13" />{{ t.blk_dup_note }}
      </p>

      <p class="pop__note">
        <Icon name="eye" :size="13" />{{ t.cal_readonly }}
      </p>
    </div>

    <!-- Дії редагування/синку відкладено в майбутні зміни — показані вимкненими. -->
    <div class="pop__foot">
      <Btn variant="primary" size="sm" icon="sync" disabled>{{ t.blk_sync }}</Btn>
      <span class="spacer" />
      <Btn variant="ghost" size="sm" icon="edit" :title="t.blk_edit_issue" disabled />
      <Btn variant="ghost" size="sm" icon="trash" :title="t.blk_delete" disabled />
    </div>
  </div>
</template>
