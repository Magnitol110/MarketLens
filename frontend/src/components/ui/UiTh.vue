<template>
  <th :class="classes" :style="{ background: 'rgba(0,0,0,0.2)' }">
    <slot />
  </th>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  align: {
    type: String,
    default: 'left' // 'left' | 'center' | 'right'
  }
})

const classes = computed(() => {
  return [
    'p-md',
    'text-xs',
    'uppercase',
    'tracking-wider',
    'text-muted',
    'font-bold',
    'border-b',
    `text-${props.align}`
  ]
})
</script>
