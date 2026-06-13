<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    initials: string
    hue?: number
    size?: number
  }>(),
  { hue: 220, size: 30 },
)

const style = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
  fontSize: `${props.size * 0.38}px`,
  background: `oklch(0.92 0.04 ${props.hue})`,
  color: `oklch(0.42 0.13 ${props.hue})`,
}))
</script>

<template>
  <span class="sw-avatar" :style="style">{{ initials }}</span>
</template>
