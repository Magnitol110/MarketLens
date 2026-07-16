<template>
  <section class="p-xl m-auto max-w-screen-xl w-full relative z-10 mb-xl">
    <div class="text-center mb-xl">
      <UiHeading level="2" class="mb-xs">How it Works</UiHeading>
      <UiText size="lg" color="secondary">A reproducible path from market history to one clear signal.</UiText>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-lg">
      <UiCard class="text-center" style="padding: 2.5rem 1.5rem;">
        <div class="text-4xl mb-md">📊</div>
        <UiHeading level="4" class="mb-sm">1. Time-aligned data</UiHeading>
        <UiText color="secondary">Daily OHLCV history is aligned with the S&amp;P 500 benchmark and split chronologically.</UiText>
      </UiCard>
      <UiCard class="text-center" style="padding: 2.5rem 1.5rem;">
        <div class="text-4xl mb-md">🧠</div>
        <UiHeading level="4" class="mb-sm">2. Leakage-safe features</UiHeading>
        <UiText color="secondary">Returns, gaps, ranges, moving ratios, volatility and calendar cycles use only information available on that date.</UiText>
      </UiCard>
      <UiCard class="text-center" style="padding: 2.5rem 1.5rem;">
        <div class="text-4xl mb-md">⚡</div>
        <UiHeading level="4" class="mb-sm">3. GPU-trained inference</UiHeading>
        <UiText color="secondary">A compact neural network estimates the probability of outperforming, matching or lagging SPY over five trading days.</UiText>
      </UiCard>
    </div>
  </section>
</template>

<script setup lang="ts">
import UiHeading from '../ui/UiHeading.vue'
import UiText from '../ui/UiText.vue'
import UiCard from '../ui/UiCard.vue'
</script>
