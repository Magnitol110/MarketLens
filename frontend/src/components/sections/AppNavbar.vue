<template>
  <nav class="flex justify-between items-center px-lg py-md max-w-screen-xl m-auto w-full relative z-10 border-b border-subtle">
    <div class="flex items-center gap-xs">
      <UiHeading level="2" gradient class="m-0 text-2xl font-extrabold">M</UiHeading>
      <UiHeading level="4" class="m-0">MarketLens</UiHeading>
    </div>
    <div class="flex items-center gap-md">
      <UiButton variant="primary" to="/app/dashboard">Open Workspace</UiButton>
    </div>
  </nav>
</template>

<script setup lang="ts">
import UiHeading from '../ui/UiHeading.vue'
import UiButton from '../ui/UiButton.vue'
</script>
