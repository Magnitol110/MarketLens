<template>
  <section class="p-xl m-auto max-w-screen-xl w-full relative z-10 mb-xl bg-[rgba(15,23,42,0.4)] border border-subtle" style="border-radius: var(--radius-lg); backdrop-filter: blur(10px);">
    <div class="text-center mb-lg">
      <UiHeading level="2" class="mb-xs">Understand the Signals</UiHeading>
      <UiText size="lg" color="secondary">One five-day horizon, expressed as three relative-market outcomes.</UiText>
    </div>

    <div class="flex flex-col gap-sm">
      <div class="flex items-center gap-md p-md border-b">
        <UiBadge variant="outperform" />
        <UiText color="secondary"><strong class="text-primary">Outperform:</strong> Model predicts this asset will beat the S&P 500 by >1% over the next 5 days.</UiText>
      </div>
      <div class="flex items-center gap-md p-md border-b">
        <UiBadge variant="neutral" />
        <UiText color="secondary"><strong class="text-primary">Neutral:</strong> Model predicts this asset will perform in-line with the broader market (±1%).</UiText>
      </div>
      <div class="flex items-center gap-md p-md">
        <UiBadge variant="underperform" />
        <UiText color="secondary"><strong class="text-primary">Underperform:</strong> Model predicts this asset will lag the S&P 500 by >1%.</UiText>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import UiHeading from '../ui/UiHeading.vue'
import UiText from '../ui/UiText.vue'
import UiBadge from '../ui/UiBadge.vue'
</script>
