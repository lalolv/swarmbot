<script setup lang="ts">
import ThemeSwitcher from "@/components/ThemeSwitcher.vue";
</script>

<template>
  <header
    class="fixed top-0 left-0 right-0 z-50 h-16 bg-card/90 backdrop-blur border-b-(length:--theme-border-width) border-border"
  >
    <div class="h-full px-3 sm:px-4 lg:px-6 flex items-center gap-3">
      <!-- Logo & Title -->
      <div class="min-w-0 flex-1 flex items-center gap-3">
        <div
          class="w-8 h-8 rounded-(--theme-radius) bg-primary flex items-center justify-center border-(length:--theme-border-width) border-border shadow-card shrink-0"
        >
          <svg class="w-5 h-5 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        </div>
        <div class="min-w-0">
          <h1 class="font-display text-base sm:text-lg leading-tight font-bold text-foreground truncate">PM Sports Bots</h1>
          <p class="hidden sm:block text-[10px] text-muted-foreground tracking-wider uppercase truncate">Task Orchestration System</p>
        </div>
      </div>

      <!-- Right: Theme Switcher -->
      <div class="flex items-center gap-2 shrink-0">
        <ThemeSwitcher compact />
      </div>
    </div>
  </header>
</template>

<style scoped>
header {
  isolation: isolate;
}
</style>
