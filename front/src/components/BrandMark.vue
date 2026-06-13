<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 28 })
</script>

<template>
  <span class="brandmark" :style="{ width: `${size}px`, height: `${size}px` }">
    <svg viewBox="0 0 32 32" :width="size" :height="size">
      <rect x="1" y="1" width="30" height="30" rx="8" fill="var(--accent)" />
      <path
        d="M9 11.5a5 5 0 0 1 8.5-2l1.5 1.5M19 9v3.5h-3.5"
        fill="none"
        stroke="#fff"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <path
        d="M23 20.5a5 5 0 0 1-8.5 2L13 21M13 23v-3.5h3.5"
        fill="none"
        stroke="#fff"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
  </span>
</template>
