<script setup lang="ts">
import { computed } from 'vue'

import Icon from '@/components/ui/Icon.vue'
import { fmtSpan, type PlacedBlock, PXMIN, syncMeta } from '@/lib/calendar'
import { fmtDur } from '@/lib/format'
import { projectColors } from '@/styles/palette'

// Один блок робочого часу. Read-only: без resize-ручок і drag — лише клік
// відкриває панель деталей. 3 варіанти (basic/soft/bold) + стани синку
// (service/tempo/synced) + forward-compat error-стиль `failed` (бекенд його
// не віддає в read-фазі, але компонент уміє малювати).
const props = withDefaults(
  defineProps<{
    block: PlacedBlock
    variant: 'basic' | 'soft' | 'bold'
    dark?: boolean
    selected?: boolean
  }>(),
  { dark: false, selected: false },
)

defineEmits<{ (e: 'select', ev: MouseEvent): void }>()

const colors = computed(() => projectColors(props.block.hue))
const meta = computed(() => syncMeta(props.block.status))
const hPx = computed(() => (props.block.gEnd - props.block.gStart) * PXMIN)
const compact = computed(() => hPx.value < 46)
const tiny = computed(() => hPx.value < 30)

const classes = computed(() => [
  'blk',
  `blk--${props.variant}`,
  `blk--${props.block.status}`,
  { 'is-selected': props.selected, 'is-compact': compact.value },
])

const style = computed<Record<string, string>>(() => {
  const c = colors.value
  const s: Record<string, string> = {}
  if (props.variant === 'basic') {
    s.background = props.dark ? c.softDark : c.base
    s.color = props.dark ? c.inkLight : '#fff'
    s['--blk-edge'] = props.dark ? c.inkLight : 'rgba(255,255,255,.85)'
    s['--blk-line'] = props.dark ? 'rgba(255,255,255,.14)' : 'rgba(255,255,255,.28)'
  } else if (props.variant === 'soft') {
    s.background = props.dark ? c.softDark : c.soft
    s.color = props.dark ? c.inkLight : c.ink
    s['--blk-edge'] = c.base
    s['--blk-line'] = props.dark ? 'rgba(255,255,255,.08)' : 'rgba(0,0,0,.06)'
    s.borderLeft = `3px solid ${c.base}`
  } else {
    s.background = props.dark
      ? `linear-gradient(160deg, ${c.softDark}, color-mix(in oklch, ${c.softDark}, #000 22%))`
      : `linear-gradient(160deg, ${c.base}, ${c.strong})`
    s.color = props.dark ? c.inkLight : '#fff'
    s['--blk-edge'] = props.dark ? c.inkLight : '#fff'
    s['--blk-line'] = props.dark ? 'rgba(255,255,255,.12)' : 'rgba(255,255,255,.22)'
  }
  return s
})

const title = computed(() => props.block.description || props.block.issueKey || '')
</script>

<template>
  <div :class="classes" :style="style" @click.stop="$emit('select', $event)">
    <div v-if="variant === 'bold'" :class="`blk__ribbon blk__ribbon--${block.status}`" />

    <div class="blk__top">
      <span class="blk__time mono">{{ fmtSpan(block.spanStart, block.spanEnd) }}</span>
      <span class="blk__corner">
        <span :class="['blk-state', `blk-state--${block.status}`, `blk-state--${variant}`]" :title="block.status">
          <Icon :name="meta.icon" :size="12" :stroke="2" :fill="block.status === 'synced'" />
        </span>
      </span>
    </div>

    <div v-if="!compact" class="blk__body">
      <div class="blk__title">{{ title }}</div>
      <div class="blk__meta">
        <span v-if="block.issueKey" class="blk__key mono">{{ block.issueKey }}</span>
        <span v-if="block.issueKey && block.project.name" class="blk__dot">·</span>
        <span v-if="block.project.name" class="blk__proj">{{ block.project.name }}</span>
      </div>
    </div>

    <div v-if="!tiny" class="blk__foot">
      <span class="blk__dur mono">{{ fmtDur(block.durMin) }}</span>
      <span v-if="!compact && block.project.key" class="blk__projcat">{{ block.project.key }}</span>
    </div>
  </div>
</template>
