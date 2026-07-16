<template>
  <tr class="border-b" style="transition: background 0.15s;" :class="{ 'hover:bg-[rgba(255,255,255,0.03)]': hoverable }">
    <slot />
  </tr>
</template>

<script setup lang="ts">
defineProps({
  hoverable: {
    type: Boolean,
    default: true
  }
})
</script>
