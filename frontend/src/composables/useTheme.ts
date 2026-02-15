import { computed } from "vue";
import { useThemeStore } from "@/stores/theme";
import { themes, type ThemeName } from "@/themes";

export function useTheme() {
  const store = useThemeStore();

  const currentTheme = computed(() => store.current);

  const isDark = computed(() => store.current === "dark");

  function setTheme(name: ThemeName) {
    store.setTheme(name);
  }

  function toggleTheme() {
    const next = store.current === "neobrutalism" ? "dark" : "neobrutalism";
    store.setTheme(next);
  }

  return {
    currentTheme,
    isDark,
    themes,
    setTheme,
    toggleTheme,
  };
}
