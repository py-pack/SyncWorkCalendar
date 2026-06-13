<script setup lang="ts" generic="T">
import { computed } from 'vue'

import Checkbox from '@/components/ui/Checkbox.vue'

import type { Column } from './types'

type Id = string | number

const props = defineProps<{
  columns: Column[]
  rows: readonly T[]
  getId: (row: T) => Id
  selectable?: boolean
  selected?: Set<Id>
  empty?: string
  rowClickable?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:selected', value: Set<Id>): void
  (e: 'rowClick', row: T): void
}>()

const sel = computed<Set<Id>>(() => props.selected ?? new Set<Id>())
const allSel = computed(
  () =>
    !!props.selectable &&
    props.rows.length > 0 &&
    props.rows.every((r) => sel.value.has(props.getId(r))),
)
const someSel = computed(
  () => !!props.selectable && props.rows.some((r) => sel.value.has(props.getId(r))),
)
const colCount = computed(() => props.columns.length + (props.selectable ? 1 : 0))

function toggleAll(): void {
  const next = new Set(sel.value)
  if (allSel.value) props.rows.forEach((r) => next.delete(props.getId(r)))
  else props.rows.forEach((r) => next.add(props.getId(r)))
  emit('update:selected', next)
}

function toggleOne(id: Id): void {
  const next = new Set(sel.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  emit('update:selected', next)
}

function colWidth(c: Column): string | undefined {
  return typeof c.width === 'number' ? `${c.width}px` : c.width
}

/** Дефолтний рендер комірки (колонки з rich-контентом дають свій слот). */
function cellText(row: T, key: string): string {
  const v = (row as Record<string, unknown>)[key]
  return v == null ? '' : String(v)
}

function onRowClick(row: T): void {
  if (props.rowClickable) emit('rowClick', row)
}
</script>

<template>
  <div class="dt-wrap">
    <table class="dt">
      <thead>
        <tr>
          <th v-if="selectable" class="dt__sel">
            <Checkbox
              :checked="allSel"
              :indeterminate="someSel && !allSel"
              @update:checked="toggleAll"
            />
          </th>
          <th
            v-for="c in columns"
            :key="c.key"
            :style="{ width: colWidth(c) }"
            :class="{ 'is-right': c.align === 'right' }"
          >
            {{ c.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="rows.length === 0">
          <td :colspan="colCount" class="dt__empty">{{ empty || '—' }}</td>
        </tr>
        <tr
          v-for="r in rows"
          :key="getId(r)"
          :class="{ 'is-sel': sel.has(getId(r)), 'is-click': rowClickable }"
          @click="onRowClick(r)"
        >
          <td v-if="selectable" class="dt__sel" @click.stop>
            <Checkbox :checked="sel.has(getId(r))" @update:checked="toggleOne(getId(r))" />
          </td>
          <td
            v-for="c in columns"
            :key="c.key"
            :style="{ textAlign: c.align }"
            :class="{ 'is-right': c.align === 'right', mono: c.mono }"
          >
            <slot :name="`cell-${c.key}`" :row="r">{{ cellText(r, c.key) }}</slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
