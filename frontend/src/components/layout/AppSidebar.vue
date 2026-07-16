<template>
  <aside class="flex flex-col border-r relative z-10 bg-[rgba(15,23,42,0.6)]" style="width: 240px; min-width: 240px;">
    <div class="flex items-center px-md border-b" style="height: 70px;">
      <div class="flex items-center gap-xs">
        <UiHeading level="2" gradient class="m-0 text-2xl font-extrabold text-gradient">M</UiHeading>
        <UiText weight="bold" size="lg" class="m-0">MarketLens</UiText>
      </div>
    </div>

    <nav class="flex-1 p-md overflow-y-auto">
      <div class="flex flex-col gap-xs mb-lg">
        <UiText size="xs" color="muted" weight="medium" class="uppercase tracking-wider px-sm mb-xs">Workspace</UiText>
        <router-link to="/app/dashboard" class="flex items-center gap-sm p-sm text-secondary font-medium" style="border-radius: var(--radius-sm); text-decoration: none;" active-class="bg-[rgba(59,130,246,0.1)] text-accent border-l-2 border-accent">
          <span class="text-md">📊</span> Dashboard
        </router-link>
      </div>
    </nav>

    <div class="p-sm border-t flex flex-col gap-sm">
      <Disclaimer />
      <router-link to="/" class="flex items-center gap-sm p-sm text-muted font-medium" style="border-radius: var(--radius-sm); text-decoration: none;">
        <span class="text-md">←</span> Exit to Landing
      </router-link>
    </div>
  </aside>
</template>

<script setup lang="ts">
import Disclaimer from '../Disclaimer.vue'
import UiHeading from '../ui/UiHeading.vue'
import UiText from '../ui/UiText.vue'
</script>
