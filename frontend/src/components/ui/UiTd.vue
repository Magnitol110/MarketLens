<template>
  <td :class="classes" :style="{ width: width }">
    <slot />
  </td>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  align: {
    type: String,
    default: 'left' // 'left' | 'center' | 'right'
  },
  width: {
    type: String,
    default: 'auto'
  }
})

const classes = computed(() => {
  return [
    'p-md',
    `text-${props.align}`
  ]
})
</script>
