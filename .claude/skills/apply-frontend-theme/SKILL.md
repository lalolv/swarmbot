---
name: apply-frontend-theme
description: Add a new theme to the Vue 3 + Tailwind CSS 4 multi-theme design system. Uses dual-attribute strategy (data-theme + data-color-scheme) with light/dark variants per theme. Use when the user asks to add a new theme or new color scheme.
---

# Apply Frontend Theme — 新增主题

向项目添加新命名主题。每个主题 CSS 文件**同时包含** light 和 dark 两套变量，无需单独的暗色文件。

---

## 需要收集的参数

- `theme_name`：kebab-case，如 `ocean`、`candy-pink`
- `theme_label`：展示名，如 `Ocean`、`Candy Pink`
- `target_dir`：前端根目录，默认 `frontend`

---

## 步骤 1 — 创建主题 CSS 文件

创建 `<target_dir>/src/themes/<theme_name>.css`，包含 light 和 dark 两个规则块：

```css
/* ===== <theme_label> — Light ===== */
[data-theme="<theme_name>"][data-color-scheme="light"] {
  --theme-background: <bg>;
  --theme-foreground: <fg>;
  --theme-card: <card-bg>;
  --theme-card-foreground: <card-fg>;
  --theme-primary: <primary>;
  --theme-primary-foreground: <primary-fg>;
  --theme-secondary: <secondary>;
  --theme-secondary-foreground: <secondary-fg>;
  --theme-accent: <accent>;
  --theme-accent-foreground: <accent-fg>;
  --theme-destructive: <destructive>;
  --theme-muted: <muted>;
  --theme-muted-foreground: <muted-fg>;
  --theme-border: <border>;
  --theme-ring: <ring>;
  --theme-surface: <surface>;
  --theme-radius: <0px | 8px | 12px>;
  --theme-border-width: <2px | 3px>;
  --theme-shadow-card: <x y blur color>;
  --theme-shadow-card-hover: <x y blur color>;
  --theme-grid: rgba(<r>, <g>, <b>, 0.15);
  --theme-robot-cyan: <color>;
  --theme-robot-purple: <color>;
  --theme-robot-pink: <color>;
  --theme-robot-green: <color>;
  --theme-robot-orange: <color>;
  --theme-robot-yellow: <color>;
  color-scheme: light;
}

/* ===== <theme_label> — Dark ===== */
[data-theme="<theme_name>"][data-color-scheme="dark"] {
  --theme-background: <dark-bg>;
  --theme-foreground: <dark-fg>;
  --theme-card: <dark-card-bg>;
  --theme-card-foreground: <dark-card-fg>;
  --theme-primary: <dark-primary>;
  --theme-primary-foreground: <dark-primary-fg>;
  --theme-secondary: <dark-secondary>;
  --theme-secondary-foreground: <dark-secondary-fg>;
  --theme-accent: <dark-accent>;
  --theme-accent-foreground: <dark-accent-fg>;
  --theme-destructive: <dark-destructive>;
  --theme-muted: <dark-muted>;
  --theme-muted-foreground: <dark-muted-fg>;
  --theme-border: <dark-border>;
  --theme-ring: <dark-ring>;
  --theme-surface: <dark-surface>;
  --theme-radius: <0px | 8px | 12px>;
  --theme-border-width: <2px | 3px>;
  --theme-shadow-card: <x y blur color>;
  --theme-shadow-card-hover: <x y blur color>;
  --theme-grid: rgba(<r>, <g>, <b>, 0.06);
  --theme-robot-cyan: <color>;
  --theme-robot-purple: <color>;
  --theme-robot-pink: <color>;
  --theme-robot-green: <color>;
  --theme-robot-orange: <color>;
  --theme-robot-yellow: <color>;
  color-scheme: dark;
}
```

**配色风格参考：**

| 风格 | 亮色背景 | 暗色背景 | 主色 | 圆角 | 边框宽 |
|------|---------|---------|------|------|--------|
| Neo-Brutalism | `#fef2e8` | `#0a0a0f` | 亮粉/霓虹青 | 0px | 3px |
| Ocean | `#f0f8ff` | `#0d1b2a` | `#06d6a0` | 8px | 2px |
| Candy | `#fff0f6` | `#1a0a2e` | `#c77dff` | 12px | 2px |
| Terminal | `#f5f5f5` | `#000000` | `#00ff41` | 0px | 1px |

> 亮色 robot palette 用中饱和度色（白底可读）；暗色用高亮霓虹色（深底发光）。

---

## 步骤 2 — 注册主题

编辑 `<target_dir>/src/themes/index.ts`，追加两处：

```typescript
// ThemeName 联合类型追加新名称
export type ThemeName = "neobrutalism" | "<theme_name>";

// THEMES 数组追加新条目
export const THEMES: ThemeDefinition[] = [
  { name: "neobrutalism", label: "Neo Brutalism" },
  { name: "<theme_name>", label: "<theme_label>" },  // 新增
];
```

---

## 步骤 3 — 导入 CSS

编辑 `<target_dir>/src/app.css`，在现有 import 行后追加：

```css
@import "./themes/neobrutalism.css";
@import "./themes/<theme_name>.css";   /* 新增 */
```

---

## 步骤 4 — 验证

```bash
# TypeScript 类型检查（零报错）
cd <target_dir> && npx vue-tsc --noEmit

# 确认两个规则块都存在
grep -c "data-color-scheme" <target_dir>/src/themes/<theme_name>.css
# 期望输出：2

# 确认 ThemeName 已更新
grep "ThemeName" <target_dir>/src/themes/index.ts
```

`ThemeSwitcher.vue` 无需修改——当 `THEMES.length > 1` 时自动显示主题卡片选择区域。

---

## 参考：变量清单（每套 28 个）

```
--theme-background  --theme-foreground
--theme-card        --theme-card-foreground
--theme-primary     --theme-primary-foreground
--theme-secondary   --theme-secondary-foreground
--theme-accent      --theme-accent-foreground
--theme-destructive
--theme-muted       --theme-muted-foreground
--theme-border      --theme-ring      --theme-surface
--theme-radius      --theme-border-width
--theme-shadow-card --theme-shadow-card-hover
--theme-grid
--theme-robot-cyan  --theme-robot-purple  --theme-robot-pink
--theme-robot-green --theme-robot-orange  --theme-robot-yellow
```

## 参考：内置主题 neobrutalism.css 完整配色

```css
/* --- Light --- */
[data-theme="neobrutalism"][data-color-scheme="light"],
:root {
  --theme-background: #fef2e8;
  --theme-foreground: #1a1a1a;
  --theme-card: #ffffff;
  --theme-card-foreground: #1a1a1a;
  --theme-primary: #ff2d95;
  --theme-primary-foreground: #ffffff;
  --theme-secondary: #00f0ff;
  --theme-secondary-foreground: #1a1a1a;
  --theme-accent: #ffee00;
  --theme-accent-foreground: #1a1a1a;
  --theme-destructive: #ff4444;
  --theme-muted: #f5f5f5;
  --theme-muted-foreground: #666666;
  --theme-border: #1a1a1a;
  --theme-ring: #1a1a1a;
  --theme-surface: #ffffff;
  --theme-radius: 0px;
  --theme-border-width: 3px;
  --theme-shadow-card: 4px 4px 0px #1a1a1a;
  --theme-shadow-card-hover: 6px 6px 0px #1a1a1a;
  --theme-grid: rgba(200, 170, 140, 0.25);
  --theme-robot-cyan: #0891b2;
  --theme-robot-purple: #7c3aed;
  --theme-robot-pink: #db2777;
  --theme-robot-green: #059669;
  --theme-robot-orange: #ea580c;
  --theme-robot-yellow: #ca8a04;
  color-scheme: light;
}

/* --- Dark --- */
[data-theme="neobrutalism"][data-color-scheme="dark"] {
  --theme-background: #0a0a0f;
  --theme-foreground: #e2e8f0;
  --theme-card: #1a1a25;
  --theme-card-foreground: #e2e8f0;
  --theme-primary: #00f0ff;
  --theme-primary-foreground: #0a0a0f;
  --theme-secondary: #b829ff;
  --theme-secondary-foreground: #ffffff;
  --theme-accent: #ff2d95;
  --theme-accent-foreground: #ffffff;
  --theme-destructive: #ff2d95;
  --theme-muted: #1a1a25;
  --theme-muted-foreground: #94a3b8;
  --theme-border: #e2e8f0;
  --theme-ring: #00f0ff;
  --theme-surface: #12121a;
  --theme-radius: 0px;
  --theme-border-width: 3px;
  --theme-shadow-card: 4px 4px 0px #00f0ff;
  --theme-shadow-card-hover: 6px 6px 0px #00f0ff;
  --theme-grid: rgba(0, 240, 255, 0.06);
  --theme-robot-cyan: #22d3ee;
  --theme-robot-purple: #a78bfa;
  --theme-robot-pink: #f472b6;
  --theme-robot-green: #34d399;
  --theme-robot-orange: #fb923c;
  --theme-robot-yellow: #facc15;
  color-scheme: dark;
}
```
