import { defineStore } from "pinia";
import { type ThemeName, DEFAULT_THEME } from "@/themes";

export const useThemeStore = defineStore("theme", {
  state: () => ({
    current: (localStorage.getItem("theme") as ThemeName) || DEFAULT_THEME,
  }),

  actions: {
    setTheme(name: ThemeName) {
      this.current = name;
      document.documentElement.setAttribute("data-theme", name);
      localStorage.setItem("theme", name);
    },

    initTheme() {
      document.documentElement.setAttribute("data-theme", this.current);
    },
  },
});
