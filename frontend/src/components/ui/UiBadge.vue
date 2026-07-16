<template>
  <div :class="classes">
    <span v-if="dot" class="ui-dot" :class="`ui-dot-${variant}`"></span>
    <slot>
      {{ variant.toUpperCase() }}
    </slot>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    required: true // 'outperform' | 'neutral' | 'underperform'
  },
  dot: {
    type: Boolean,
    default: true
  }
})

const classes = computed(() => {
  return [
    'ui-badge',
    `ui-badge-${props.variant}`
  ]
})
</script>
