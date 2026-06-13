<script setup lang="ts">
import { computed } from 'vue'

import { hueFor } from '@/lib/format'
import { projectColors } from '@/styles/palette'

// Кольоровий тег проекту. hue — або заданий, або детермінований із label.
const props = defineProps<{ label: string; hue?: number }>()
const colors = computed(() => projectColors(props.hue ?? hueFor(props.label)))
</script>

<template>
  <span class="projtag" :style="{ background: colors.soft, color: colors.ink }">
    <span class="projtag__dot" :style="{ background: colors.base }" />
    {{ label }}
  </span>
</template>
