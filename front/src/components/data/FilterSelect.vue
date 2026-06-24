<script setup lang="ts">
// Невеликий переюзовний select-фільтр на патерні поповера Menu.vue
// (click-outside + Esc), без зовнішньої бібліотеки (rework-jira-issues-screen,
// D9). Значення — рядок або null (null = «усі», знімає фільтр). Опційний пошук
// по опціях (для довгих списків — напр. проектів).
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import Btn from '@/components/ui/Btn.vue'

interface Option {
  value: string
  label: string
  /** Тьмянити опцію (напр. архівний проект). */
  dim?: boolean
}

const props = withDefaults(
  defineProps<{
    modelValue: string | null
    options: Option[]
    allLabel: string
    placeholder?: string
    searchable?: boolean
  }>(),
  { searchable: false, placeholder: '' },
)
const emit = defineEmits<{ (e: 'update:modelValue', value: string | null): void }>()

const open = ref(false)
const root = ref<HTMLElement | null>(null)
const query = ref('')

const selectedLabel = computed(() => {
  if (props.modelValue === null) return props.allLabel
  return props.options.find((o) => o.value === props.modelValue)?.label ?? props.modelValue
})

const filtered = computed(() => {
  const text = query.value.trim().toLowerCase()
  if (!text) return props.options
  return props.options.filter((o) => o.label.toLowerCase().includes(text))
})

function pick(value: string | null): void {
  emit('update:modelValue', value)
  open.value = false
  query.value = ''
}
function toggle(): void {
  open.value = !open.value
  if (!open.value) query.value = ''
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
  <div ref="root" class="fsel">
    <Btn
      variant="default"
      size="sm"
      icon-right="chevD"
      :class="{ 'is-on': modelValue !== null }"
      @click="toggle"
    >
      {{ selectedLabel }}
    </Btn>

    <div v-if="open" class="fsel__pop">
      <input
        v-if="searchable"
        v-model="query"
        class="sw-input fsel__search"
        :placeholder="placeholder"
      />
      <div class="fsel__opts">
        <button
          type="button"
          :class="['fsel__opt', { 'is-on': modelValue === null }]"
          @click="pick(null)"
        >
          {{ allLabel }}
        </button>
        <button
          v-for="o in filtered"
          :key="o.value"
          type="button"
          :class="['fsel__opt', { 'is-on': modelValue === o.value, 'is-dim': o.dim }]"
          @click="pick(o.value)"
        >
          {{ o.label }}
        </button>
      </div>
    </div>
  </div>
</template>
