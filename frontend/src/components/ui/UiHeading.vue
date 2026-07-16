<template>
  <component :is="tag" :class="classes" :style="styles">
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  level: {
    type: [Number, String],
    default: 1
  },
  gradient: {
    type: Boolean,
    default: false
  },
  tight: {
    type: Boolean,
    default: false
  }
})

const tag = computed(() => `h${props.level}`)

const classes = computed(() => {
  const map: Record<string, string> = {
    '1': 'text-4xl font-extrabold',
    '2': 'text-3xl font-bold',
    '3': 'text-2xl font-bold',
    '4': 'text-xl font-bold'
  }

  return [
    map[props.level.toString()] || map['1'],
    props.gradient ? 'text-gradient' : 'text-primary'
  ]
})

const styles = computed(() => {
  return {
    letterSpacing: props.level === 1 ? '-0.02em' : 'normal',
    lineHeight: props.tight ? '1.1' : '1.3'
  }
})
</script>
