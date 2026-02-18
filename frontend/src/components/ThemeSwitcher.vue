<script setup lang="ts">
import { computed, ref } from "vue";

import { useTheme } from "@/composables/useTheme";
import { DropdownPopover } from "@/components/ui/dropdown";
import type { ColorMode, ThemeName } from "@/themes";

const props = withDefaults(
  defineProps<{
    compact?: boolean;
  }>(),
  {
    compact: false,
  }
);

const { mode, themeName, themes, setMode, setTheme } = useTheme();

const panelOpen = ref(false);

const colorOptions: { value: ColorMode; title: string; shortLabel: string }[] = [
  { value: "light", title: "亮色模式", shortLabel: "亮" },
  { value: "system", title: "跟随系统", shortLabel: "系统" },
  { value: "dark", title: "暗色模式", shortLabel: "暗" },
];

const activeThemeLabel = computed(() => {
  return themes.find((item) => item.name === themeName.value)?.label ?? themeName.value;
});

function selectTheme(name: ThemeName, close?: (restoreFocus?: boolean) => void) {
  setTheme(name);
  if (props.compact && close) {
    close();
  }
}

function selectMode(nextMode: ColorMode) {
  setMode(nextMode);
}
</script>

<template>
  <DropdownPopover
    v-if="compact"
    v-model:open="panelOpen"
    panel-id="theme-control-panel"
    panel-class="absolute right-0 top-full mt-2 w-[280px] bg-card border-(length:--theme-border-width) border-border rounded-(--theme-radius) shadow-card-hover overflow-hidden animate-slide-down z-50"
  >
    <template #trigger="{ open, toggle }">
      <button
        type="button"
        class="h-8 px-3 inline-flex items-center gap-2 text-xs font-display font-semibold border-(length:--theme-border-width) border-border rounded-(--theme-radius) bg-surface text-foreground shadow-card hover:-translate-y-0.5 hover:shadow-card-hover active:translate-y-0 transition-all"
        :aria-expanded="open"
        aria-controls="theme-control-panel"
        aria-haspopup="true"
        @click="toggle"
      >
        <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 3c1.8 0 3.5.8 4.6 2.1 1.8.1 3.4 1.3 4 3 .6 1.7.2 3.6-1 4.9.3 1.8-.4 3.6-1.9 4.8-1.4 1.1-3.4 1.3-5 .5-1.6.8-3.6.6-5-.5-1.5-1.2-2.2-3-1.9-4.8-1.2-1.3-1.6-3.2-1-4.9.6-1.7 2.2-2.9 4-3C8.5 3.8 10.2 3 12 3z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6M12 9v6" />
        </svg>
        <span class="hidden md:inline text-xs font-display font-semibold">{{ activeThemeLabel }}</span>
        <svg class="w-4 h-4 transition-transform" :class="{ 'rotate-180': open }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
    </template>

    <template #default="{ close }">
      <div class="px-3 py-2 border-b border-border bg-muted/40">
        <p class="text-[10px] font-mono uppercase tracking-[0.18em] text-muted-foreground">Theme Control</p>
      </div>

      <div class="p-3 space-y-3">
        <div v-if="themes.length > 1" class="space-y-1.5">
          <p class="text-[11px] text-muted-foreground font-display font-semibold uppercase tracking-wider">主题列表</p>
          <div class="space-y-1">
            <button
              v-for="t in themes"
              :key="t.name"
              type="button"
              class="w-full h-9 px-2.5 text-xs font-display font-semibold border-(length:--theme-border-width) border-border rounded-(--theme-radius) transition-all flex items-center justify-between"
              :class="themeName === t.name ? 'bg-primary text-primary-foreground shadow-card' : 'bg-surface text-foreground hover:bg-muted'"
              @click="selectTheme(t.name as ThemeName, close)"
            >
              <span>{{ t.label }}</span>
              <span v-if="themeName === t.name" class="text-[10px] opacity-85">当前</span>
            </button>
          </div>
        </div>

        <div class="space-y-1.5">
          <p class="text-[11px] text-muted-foreground font-display font-semibold uppercase tracking-wider">色彩模式</p>
          <div class="flex border-(length:--theme-border-width) border-border rounded-(--theme-radius) overflow-hidden">
            <button
              v-for="(opt, i) in colorOptions"
              :key="opt.value"
              type="button"
              :title="opt.title"
              :aria-pressed="mode === opt.value"
              class="relative flex-1 h-9 text-xs font-display font-semibold transition-all"
              :class="mode === opt.value ? 'bg-secondary text-secondary-foreground' : 'bg-surface text-muted-foreground hover:text-foreground hover:bg-muted'"
              @click="selectMode(opt.value)"
            >
              <span>{{ opt.shortLabel }}</span>
              <span
                v-if="i > 0"
                class="absolute left-0 top-1.5 bottom-1.5 bg-border"
                :style="{ width: 'var(--theme-border-width)' }"
              />
            </button>
          </div>
        </div>
      </div>
    </template>
  </DropdownPopover>

  <div v-else class="flex flex-col gap-3">
    <div v-if="themes.length > 1" class="flex flex-col gap-1.5">
      <span class="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">主题</span>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="t in themes"
          :key="t.name"
          @click="selectTheme(t.name as ThemeName)"
          :aria-pressed="themeName === t.name"
          class="px-3 h-8 text-xs font-display font-bold border-(length:--theme-border-width) border-border rounded-(--theme-radius) transition-all hover:-translate-y-0.5 active:translate-y-0"
          :class="themeName === t.name ? 'bg-primary text-primary-foreground shadow-card' : 'bg-surface text-muted-foreground hover:text-foreground hover:bg-muted'"
        >
          {{ t.label }}
        </button>
      </div>
    </div>

    <div
      class="flex border-(length:--theme-border-width) border-border rounded-(--theme-radius) overflow-hidden shadow-card"
      role="group"
      aria-label="色彩方案"
    >
      <button
        v-for="(opt, i) in colorOptions"
        :key="opt.value"
        @click="selectMode(opt.value)"
        :title="opt.title"
        :aria-pressed="mode === opt.value"
        class="relative w-9 h-9 flex items-center justify-center transition-all hover:-translate-y-0.5 active:translate-y-0"
        :class="mode === opt.value ? 'bg-primary text-primary-foreground' : 'bg-surface text-muted-foreground hover:text-foreground hover:bg-muted'"
      >
        <span
          v-if="i > 0"
          class="absolute left-0 top-1.5 bottom-1.5 bg-border"
          :style="{ width: 'var(--theme-border-width)' }"
        />

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
