<script setup lang="ts">
import { ref } from 'vue'

import IconBtn from '@/components/ui/IconBtn.vue'
import Segmented from '@/components/ui/Segmented.vue'
import Toggle from '@/components/ui/Toggle.vue'
import { useI18n } from '@/i18n'
import { ACCENT_OPTIONS } from '@/styles/palette'
import { useUiStore, type Density } from '@/stores/ui'

// Спрощена in-app панель Tweaks (без drag/postMessage редактор-харнеса
// прототипу): акцент, щільність, смуга робочих годин, вихідні.
const { lang } = useI18n()
const ui = useUiStore()
const open = ref(false)

const L = (uk: string, en: string): string => (lang.value === 'uk' ? uk : en)
</script>

<template>
  <div class="twk">
    <div v-if="open" class="twk__panel">
      <div class="twk__section">{{ L('Акцент', 'Accent') }}</div>
      <div class="twk__row">
        <span class="twk__label">{{ L('Колір', 'Color') }}</span>
        <div class="twk__colors">
          <button
            v-for="c in ACCENT_OPTIONS"
            :key="c"
            type="button"
            :class="['twk__color', { 'is-active': ui.accent === c }]"
            :style="{ background: c }"
            :title="c"
            @click="ui.setAccent(c)"
          />
        </div>
      </div>

      <div class="twk__section">{{ L('Щільність', 'Density') }}</div>
      <div class="twk__row">
        <span class="twk__label">{{ L('Інтерфейс', 'Layout') }}</span>
        <Segmented
          size="sm"
          :model-value="ui.density"
          :options="[
            { value: 'compact', label: L('Компактно', 'Compact') },
            { value: 'regular', label: L('Звичайно', 'Regular') },
          ]"
          @update:model-value="(v: string) => ui.setDensity(v as Density)"
        />
      </div>

      <div class="twk__section">{{ L('Календар', 'Calendar') }}</div>
      <div class="twk__row">
        <span class="twk__label">{{ L('Смуга робочих годин', 'Work-hours band') }}</span>
        <Toggle :checked="ui.workBand" size="sm" @update:checked="ui.workBand = $event" />
      </div>
      <div class="twk__row">
        <span class="twk__label">{{ L('Показувати вихідні', 'Show weekends') }}</span>
        <Toggle :checked="ui.weekends" size="sm" @update:checked="ui.weekends = $event" />
      </div>
    </div>

    <IconBtn
      :name="open ? 'x' : 'settings'"
      variant="outline"
      :title="L('Налаштування вигляду', 'Appearance tweaks')"
      @click="open = !open"
    />
  </div>
</template>
