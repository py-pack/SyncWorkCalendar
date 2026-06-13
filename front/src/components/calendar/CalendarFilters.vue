<script setup lang="ts">
import Icon from '@/components/ui/Icon.vue'
import { useI18n } from '@/i18n'
import { syncMeta } from '@/lib/calendar'
import { projectColors } from '@/styles/palette'
import { useCalendarStore } from '@/stores/calendar'

const { t } = useI18n()
const store = useCalendarStore()
</script>

<template>
  <div class="cal__filters">
    <div class="cal__fgroup">
      <span class="cal__flabel">{{ t.cal_projects }}</span>
      <div class="cal__chips">
        <button
          v-for="p in store.projects"
          :key="p.id"
          :class="['chip', { 'is-on': p.on }]"
          @click="store.toggleProj(p.id)"
        >
          <span
            class="chip__dot"
            :style="{ background: p.on ? projectColors(p.hue).base : 'var(--text-faint)' }"
          />
          {{ p.name }}
        </button>
      </div>
    </div>

    <div class="cal__fsep" />

    <div class="cal__fgroup">
      <span class="cal__flabel">{{ t.cal_status }}</span>
      <div class="cal__chips">
        <button
          v-for="s in store.statuses"
          :key="s.status"
          :class="['chip', { 'is-on': s.on }]"
          @click="store.toggleStatus(s.status)"
        >
          <Icon :name="syncMeta(s.status).icon" :size="13" />
          {{ t[syncMeta(s.status).shortKey] }}
        </button>
      </div>
    </div>
  </div>
</template>
