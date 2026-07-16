<template>
  <div :class="classes">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  glass: {
    type: Boolean,
    default: false
  },
  noPadding: {
    type: Boolean,
    default: false
  }
})

const classes = computed(() => {
  return [
    'ui-card',
    {
      'glass': props.glass,
      'no-padding': props.noPadding
    }
  ]
})
</script>
