<template>
  <div :class="classes" :style="{ maxWidth: maxW }">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  size: {
    type: String,
    default: 'xl' // md, lg, xl, 2xl
  },
  centered: {
    type: Boolean,
    default: true
  },
  padded: {
    type: Boolean,
    default: true
  }
})

const classes = computed(() => {
  return [
    props.centered ? 'm-auto' : '',
    props.padded ? 'p-xl' : '',
    'w-full'
  ]
})

const maxW = computed(() => {
  const map: Record<string, string> = {
    'md': '800px',
    'lg': '1024px',
    'xl': '1280px',
    '2xl': '1600px'
  }
  return map[props.size] || map['xl']
})
</script>
