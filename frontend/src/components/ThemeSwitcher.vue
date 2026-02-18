<script setup lang="ts">
import { useTheme } from "@/composables/useTheme";
import type { ColorMode, ThemeName } from "@/themes";

const { mode, themeName, themes, setMode, setTheme } = useTheme();

const colorOptions: { value: ColorMode; title: string }[] = [
  { value: "light", title: "亮色模式" },
  { value: "system", title: "跟随系统" },
  { value: "dark", title: "暗色模式" },
];
</script>

<template>
  <div class="flex flex-col gap-3">
    <!-- 主题选择（仅多主题时显示） -->
    <div v-if="themes.length > 1" class="flex flex-col gap-1.5">
      <span class="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">主题</span>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="t in themes"
          :key="t.name"
          @click="setTheme(t.name as ThemeName)"
          :aria-pressed="themeName === t.name"
          class="px-3 h-8 text-xs font-display font-bold border-(length:--theme-border-width) border-border rounded-(--theme-radius) transition-all hover:-translate-y-0.5 active:translate-y-0"
          :class="
            themeName === t.name
              ? 'bg-primary text-primary-foreground shadow-card'
              : 'bg-surface text-muted-foreground hover:text-foreground hover:bg-muted'
          "
        >
          {{ t.label }}
        </button>
      </div>
    </div>

    <!-- 色彩方案切换 -->
    <div
      class="flex border-(length:--theme-border-width) border-border rounded-(--theme-radius) overflow-hidden shadow-card"
      role="group"
      aria-label="色彩方案"
    >
      <button
        v-for="(opt, i) in colorOptions"
        :key="opt.value"
        @click="setMode(opt.value)"
        :title="opt.title"
        :aria-pressed="mode === opt.value"
        class="relative w-9 h-9 flex items-center justify-center transition-all hover:-translate-y-0.5 active:translate-y-0"
        :class="
          mode === opt.value
            ? 'bg-primary text-primary-foreground'
            : 'bg-surface text-muted-foreground hover:text-foreground hover:bg-muted'
        "
      >
        <!-- 分割线 -->
        <span
          v-if="i > 0"
          class="absolute left-0 top-1.5 bottom-1.5 bg-border"
          :style="{ width: 'var(--theme-border-width)' }"
        />

        <!-- 太阳图标（亮色） -->
        <svg
          v-if="opt.value === 'light'"
          class="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>

        <!-- 显示器图标（跟随系统） -->
        <svg
          v-else-if="opt.value === 'system'"
          class="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
          />
        </svg>

        <!-- 月亮图标（暗色） -->
        <svg
          v-else
          class="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
          />
        </svg>
      </button>
    </div>
  </div>
</template>
