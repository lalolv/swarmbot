// 主题名称（扩展时在此添加新名称）
export type ThemeName = "neobrutalism";

// 用户可选择的色彩模式：亮色 / 暗色 / 跟随系统
export type ColorMode = "light" | "dark" | "system";

// 实际渲染时使用的色彩方案（resolved，用于 DOM 属性）
export type ColorScheme = "light" | "dark";

export interface ThemeDefinition {
  name: ThemeName;
  label: string;
}

export const THEMES: ThemeDefinition[] = [
  { name: "neobrutalism", label: "Neo Brutalism" },
];

export const DEFAULT_THEME: ThemeName = "neobrutalism";
export const DEFAULT_MODE: ColorMode = "system";
