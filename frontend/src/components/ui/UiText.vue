<template>
  <component :is="as" :class="classes">
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  as: {
    type: String,
    default: 'p' // p, span, div
  },
  color: {
    type: String,
    default: 'primary' // primary, secondary, muted, accent, positive, negative
  },
  size: {
    type: String,
    default: 'md' // xs, sm, md, lg, xl
  },
  weight: {
    type: String,
    default: 'normal' // normal, medium, bold, extrabold
  },
  mono: {
    type: Boolean,
    default: false
  }
})

const classes = computed(() => {
  return [
    `text-${props.color}`,
    `text-${props.size}`,
    props.weight !== 'normal' ? `font-${props.weight}` : '',
    props.mono ? 'font-mono' : '',
    props.as === 'p' ? 'mb-0' : ''
  ]
})
</script>
