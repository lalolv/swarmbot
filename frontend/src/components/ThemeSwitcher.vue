<script setup lang="ts">
import { useTheme } from "@/composables/useTheme";

const { currentTheme, isDark, toggleTheme } = useTheme();
</script>

<template>
  <button
    @click="toggleTheme"
    class="relative w-10 h-10 flex items-center justify-center rounded-(--theme-radius) transition-all
           bg-surface border-(length:--theme-border-width) border-border
           hover:shadow-card-hover hover:-translate-y-0.5 active:translate-y-0 active:shadow-card"
    :title="isDark ? '切换到亮色主题' : '切换到暗色主题'"
  >
    <!-- Sun icon (neobrutalism active) -->
    <svg
      v-if="!isDark"
      class="w-5 h-5 text-foreground"
      fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
    >
      <path stroke-linecap="round" stroke-linejoin="round"
        d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>

    <!-- Moon icon (dark active) -->
    <svg
      v-else
      class="w-5 h-5 text-foreground"
      fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
    >
      <path stroke-linecap="round" stroke-linejoin="round"
        d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
    </svg>
  </button>
</template>
