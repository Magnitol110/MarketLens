<template>
  <header class="flex-1 flex flex-col items-center justify-center text-center p-xl m-auto max-w-screen-xl relative z-10 min-h-[60vh] mt-xl mb-xl">
    <UiHeading level="1" tight class="mb-md">
      Explain market signals with <span class="text-gradient">Machine Learning</span>
    </UiHeading>
    <UiText size="xl" color="secondary" class="mb-lg max-w-[800px] m-auto" style="line-height: 1.5;">
      MarketLens turns daily market history into probability-based, five-day signals that are easy to inspect and explain. The demo starts with one trained US equity model and is designed to expand.
    </UiText>
    <div class="flex gap-md justify-center">
      <UiButton variant="primary" to="/app/dashboard" style="padding: 16px 32px; font-size: 1.1rem;">
        Explore Signals
      </UiButton>
    </div>
  </header>
</template>

<script setup lang="ts">
import UiHeading from '../ui/UiHeading.vue'
import UiText from '../ui/UiText.vue'
import UiButton from '../ui/UiButton.vue'
</script>
