export type ThemeName = "neobrutalism" | "dark";

export interface ThemeInfo {
  name: ThemeName;
  label: string;
  icon: string;
}

export const themes: ThemeInfo[] = [
  { name: "neobrutalism", label: "Neo Brutalism", icon: "sun" },
  { name: "dark", label: "Dark", icon: "moon" },
];

export const DEFAULT_THEME: ThemeName = "neobrutalism";
