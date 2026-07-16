<template>
  <footer class="mt-auto py-xl border-t bg-[rgba(0,0,0,0.5)] border-subtle text-center">
    <div class="max-w-screen-xl m-auto px-lg">
      <div class="flex justify-center mb-md">
        <Disclaimer />
      </div>
      <UiText size="sm" color="muted" class="mt-md">
        © 2026 MarketLens. Open-source educational ML project.
        <a href="https://github.com/Magnitol110/MarketLens" target="_blank" rel="noreferrer" class="text-accent underline" style="text-decoration: underline;">View on GitHub</a>
      </UiText>
    </div>
  </footer>
</template>

<script setup lang="ts">
import Disclaimer from '../Disclaimer.vue'
import UiText from '../ui/UiText.vue'
</script>
