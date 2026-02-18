import { defineStore } from "pinia";
import {
  type ThemeName,
  type ColorMode,
  type ColorScheme,
  DEFAULT_THEME,
  DEFAULT_MODE,
  THEMES,
} from "@/themes";

const VALID_MODES: ColorMode[] = ["light", "dark", "system"];
const VALID_THEME_NAMES: ThemeName[] = THEMES.map((t) => t.name);

function readStoredMode(): ColorMode {
  const stored = localStorage.getItem("theme-mode");
  return VALID_MODES.includes(stored as ColorMode)
    ? (stored as ColorMode)
    : DEFAULT_MODE;
}

function readStoredThemeName(): ThemeName {
  const stored = localStorage.getItem("theme-name");
  return VALID_THEME_NAMES.includes(stored as ThemeName)
    ? (stored as ThemeName)
    : DEFAULT_THEME;
}

export const useThemeStore = defineStore("theme", {
  state: () => ({
    themeName: readStoredThemeName(),
    mode: readStoredMode(),
    _systemDark: window.matchMedia("(prefers-color-scheme: dark)").matches,
  }),

  getters: {
    isDark(): boolean {
      if (this.mode === "system") return this._systemDark;
      return this.mode === "dark";
    },

    colorScheme(): ColorScheme {
      return this.isDark ? "dark" : "light";
    },
  },

  actions: {
    setTheme(name: ThemeName) {
      this.themeName = name;
      localStorage.setItem("theme-name", name);
      this._applyTheme();
    },

    setMode(mode: ColorMode) {
      this.mode = mode;
      localStorage.setItem("theme-mode", mode);
      this._applyTheme();
    },

    _applyTheme() {
      document.documentElement.setAttribute("data-theme", this.themeName);
      document.documentElement.setAttribute(
        "data-color-scheme",
        this.colorScheme
      );
    },

    initTheme() {
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      mq.addEventListener("change", (e) => {
        this._systemDark = e.matches;
        if (this.mode === "system") this._applyTheme();
      });
      this._applyTheme();
    },
  },
});
