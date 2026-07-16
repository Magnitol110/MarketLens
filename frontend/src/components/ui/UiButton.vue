<template>
  <component :is="tag" :class="classes" :to="to">
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary', // 'primary' | 'secondary'
  },
  to: {
    type: String,
    default: undefined,
  },
  block: {
    type: Boolean,
    default: false,
  }
})

const tag = computed(() => (props.to ? 'router-link' : 'button'))

const classes = computed(() => {
  return [
    'ui-btn',
    `ui-btn-${props.variant}`,
    { block: props.block }
  ]
})
</script>
