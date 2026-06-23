<script setup lang="ts">
// Компактний вибір періоду (rework-timecamp-entries-screen, D9). Одна кнопка
// (іконка календаря + підпис діапазону / назва активного шаблону) розкриває
// dropdown зі швидкими шаблонами всередині + ручні start/end. Поповер за
// патерном Menu.vue (click-outside + Esc); без зовнішньої бібліотеки. v-model.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import type { Period } from '@/api/types'
import Btn from '@/components/ui/Btn.vue'
import { useI18n } from '@/i18n'
import { PERIOD_PRESETS, type PeriodPreset } from '@/lib/period'

const props = defineProps<{ modelValue: Period }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: Period): void }>()

const { t } = useI18n()
const open = ref(false)
const root = ref<HTMLElement | null>(null)

function ddmm(iso: string): string {
  const [, m, d] = iso.split('-')
  return `${d}.${m}`
}

// Якщо поточний діапазон точно збігається з пресетом — у підписі його назва.
const activePreset = computed(() =>
  PERIOD_PRESETS.find((p) => {
    const r = p.range()
    return r.start === props.modelValue.start && r.end === props.modelValue.end
  }),
)
const label = computed(() =>
  activePreset.value
    ? t.value[activePreset.value.labelKey]
    : `${ddmm(props.modelValue.start)} – ${ddmm(props.modelValue.end)}`,
)

function applyPreset(p: PeriodPreset): void {
  emit('update:modelValue', p.range())
  open.value = false
}
function onStart(e: Event): void {
  const start = (e.target as HTMLInputElement).value
  if (start) emit('update:modelValue', { start, end: props.modelValue.end })
}
function onEnd(e: Event): void {
  const end = (e.target as HTMLInputElement).value
  if (end) emit('update:modelValue', { start: props.modelValue.start, end })
}

function onPointerDown(e: Event): void {
  if (root.value && !root.value.contains(e.target as Node)) open.value = false
}
function onKey(e: KeyboardEvent): void {
  if (e.key === 'Escape') open.value = false
}
onMounted(() => {
  document.addEventListener('mousedown', onPointerDown)
  document.addEventListener('touchstart', onPointerDown)
  document.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onPointerDown)
  document.removeEventListener('touchstart', onPointerDown)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <div ref="root" class="tcpp">
    <Btn variant="default" size="sm" icon="calendar" icon-right="chevD" @click="open = !open">
      {{ label }}
    </Btn>

    <div v-if="open" class="tcpp__pop">
      <div class="tcpp__presets">
        <button
          v-for="p in PERIOD_PRESETS"
          :key="p.id"
          type="button"
          :class="['tcpp__preset', { 'is-on': activePreset?.id === p.id }]"
          @click="applyPreset(p)"
        >
          {{ t[p.labelKey] }}
        </button>
      </div>

      <div class="tcpp__div" />

      <div class="tcpp__custom">
        <label class="tcpp__field">
          <span>{{ t.tcsync_from }}</span>
          <input type="date" class="sw-input" :value="modelValue.start" @change="onStart" />
        </label>
        <label class="tcpp__field">
          <span>{{ t.tcsync_to }}</span>
          <input type="date" class="sw-input" :value="modelValue.end" @change="onEnd" />
        </label>
      </div>
    </div>
  </div>
</template>
