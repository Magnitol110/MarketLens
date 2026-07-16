<template>
  <div class="flex flex-1 w-full app-bg overflow-hidden">
    <!-- Sidebar -->
    <AppSidebar />

    <!-- Main Content Area -->
    <main class="flex-1 overflow-y-auto relative flex flex-col">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" class="flex-1" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import AppSidebar from '../components/layout/AppSidebar.vue'
</script>

<style>
/* Specific transitions and ad-hoc inline styles kept minimal */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease-in-out, transform 0.15s ease-in-out;
}
.fade-enter-from { opacity: 0; transform: translateY(5px); }
.fade-leave-to { opacity: 0; transform: translateY(-5px); }

/* Utility additions for specific overrides */
.border-l-2 { border-left-width: 2px; border-left-style: solid; }
.border-accent { border-color: var(--accent-primary); }
</style>
