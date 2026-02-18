import { computed } from "vue";
import { useThemeStore } from "@/stores/theme";
import { type ThemeName, type ColorMode, THEMES } from "@/themes";

export function useTheme() {
  const store = useThemeStore();

  return {
    themeName: computed(() => store.themeName),
    mode: computed(() => store.mode),
    isDark: computed(() => store.isDark),
    colorScheme: computed(() => store.colorScheme),
    themes: THEMES,
    setTheme: (name: ThemeName) => store.setTheme(name),
    setMode: (mode: ColorMode) => store.setMode(mode),
  };
}
