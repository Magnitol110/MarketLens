<template>
  <div class="marketing-bg text-primary relative overflow-y-auto overflow-x-hidden flex flex-col flex-1">
    <AppNavbar />
    <HeroSection />
    <HowItWorksSection />
    <SignalsSection />
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import AppNavbar from '../components/sections/AppNavbar.vue'
import HeroSection from '../components/sections/HeroSection.vue'
import HowItWorksSection from '../components/sections/HowItWorksSection.vue'
import SignalsSection from '../components/sections/SignalsSection.vue'
import AppFooter from '../components/sections/AppFooter.vue'
</script>

<style>
/* Added a few specific utility layout classes */
.grid { display: grid; }
.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
@media (min-width: 768px) {
  .md\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
</style>
