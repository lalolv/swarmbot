---
name: apply-frontend-theme
description: Add, modify, or extend the dual-theme (Neo-Brutalism / Dark) CSS variable design system for Vue 3 + Tailwind CSS 4 frontends. Use when the user asks to add a new theme, change theme colors, customize the design system, adjust typography or spacing tokens, or integrate the theme system into a new project.
---

# Apply Frontend Theme

为 Vue 3 + Tailwind CSS 4 项目添加、修改或扩展主题系统。支持 CSS 变量 + `data-theme` 属性切换方案，内置 Neo-Brutalism（亮色粗粝风格）和 Dark（霓虹暗色风格）双主题。

---

## 第 0 步 — 识别场景并收集参数

**首先**询问用户属于哪种操作，然后收集对应参数：

| 场景 | 用户描述关键词 | 需要收集的参数 |
|------|--------------|--------------|
| **A** 新增主题 | "添加主题"、"新主题"、"第三套配色" | `theme_name`（kebab-case）、`theme_label`（展示名）、`color_scheme`（light/dark）、`target_dir` |
| **B** 修改现有主题 | "改颜色"、"换主色"、"调边框" | `target_theme`（neobrutalism/dark/其他）、需要修改的变量名及新值 |
| **C** 集成到新项目 | "添加主题系统"、"从零配置" | `target_dir`（前端根目录） |
| **D** 调整 token/特效 | "加 Tailwind 类"、"添加玻璃效果"、"新增动画" | `target_dir`、具体 token 名或效果描述 |

**参数校验规则：**
- `theme_name`：仅含小写字母、数字、连字符，如 `ocean`、`candy-pink`
- `color_scheme`：必须为 `light` 或 `dark`
- `target_dir`：不能是根目录；若未指定，默认为 `frontend`

---

## 第 1 步 — 检查前置条件

在执行任何操作前，运行以下命令确认项目状态：

```bash
# 检查主题系统是否已存在
ls <target_dir>/src/themes/

# 检查 app.css 是否已有 @theme 块
grep -n "@theme\|@import.*themes" <target_dir>/src/app.css

# 检查 Pinia store 是否存在
ls <target_dir>/src/stores/theme.ts <target_dir>/src/composables/useTheme.ts 2>/dev/null || echo "MISSING"
```

**根据结果判断：**
- `src/themes/` 不存在 → 先执行**场景 C**（集成主题系统），再回到目标场景
- 主题系统已存在 → 直接执行对应场景

---

## 场景 A — 新增主题

### A-1：创建主题 CSS 文件

创建 `<target_dir>/src/themes/<theme_name>.css`，参照内置主题规格填写所有 CSS 变量（见文末参考）：

```css
[data-theme="<theme_name>"] {
  /* ===== 基础色板 ===== */
  --theme-background: <bg>;
  --theme-foreground: <fg>;
  --theme-card: <card-bg>;
  --theme-card-foreground: <card-fg>;

  /* ===== 语义色 ===== */
  --theme-primary: <primary>;
  --theme-primary-foreground: <primary-fg>;
  --theme-secondary: <secondary>;
  --theme-secondary-foreground: <secondary-fg>;
  --theme-accent: <accent>;
  --theme-accent-foreground: <accent-fg>;
  --theme-destructive: <destructive>;

  /* ===== 功能色 ===== */
  --theme-muted: <muted>;
  --theme-muted-foreground: <muted-fg>;
  --theme-border: <border>;
  --theme-ring: <ring>;
  --theme-surface: <surface>;

  /* ===== 形状系统 ===== */
  --theme-radius: <0px | 8px | 12px>;
  --theme-border-width: <2px | 3px>;

  /* ===== 阴影系统 ===== */
  --theme-shadow-card: <offset-x offset-y blur color>;
  --theme-shadow-card-hover: <offset-x offset-y blur color>;

  /* ===== 画布网格 ===== */
  --theme-grid: rgba(<r>, <g>, <b>, <0.05~0.25>);

  /* ===== 机器人色板（6 色）===== */
  --theme-robot-cyan: <color>;
  --theme-robot-purple: <color>;
  --theme-robot-pink: <color>;
  --theme-robot-green: <color>;
  --theme-robot-orange: <color>;
  --theme-robot-yellow: <color>;

  color-scheme: <color_scheme>;
}
```

**配色参考：**

| 主题风格 | 背景 | 主色 | 圆角 | 边框宽度 | 阴影风格 |
|---------|------|------|------|---------|---------|
| Neo-Brutalism | 温暖米色 `#fef2e8` | 粉红 `#ff2d95` | 0px | 3px | 硬偏移黑色 |
| Dark/Neon | 深黑 `#0a0a0f` | 霓虹青 `#00f0ff` | 0px | 3px | 霓虹色偏移 |
| Ocean | 深蓝绿 `#0d1b2a` | 青绿 `#06d6a0` | 8px | 2px | 柔和蓝 |
| Candy | 粉白 `#fff0f6` | 粉紫 `#c77dff` | 12px | 2px | 粉色软阴影 |
| Terminal | 纯黑 `#000000` | 绿色 `#00ff41` | 0px | 1px | 无阴影 |

### A-2：注册主题

编辑 `<target_dir>/src/themes/index.ts`，添加新类型和列表项：

```typescript
// 在 ThemeName 联合类型中新增
export type ThemeName = "neobrutalism" | "dark" | "<theme_name>";

// 在 themes 数组中新增
export const themes: ThemeInfo[] = [
  { name: "neobrutalism", label: "Neo Brutalism", icon: "sun" },
  { name: "dark",         label: "Dark",          icon: "moon" },
  { name: "<theme_name>", label: "<theme_label>", icon: "<icon>" },
];
```

### A-3：导入 CSS

编辑 `<target_dir>/src/app.css`，在已有 import 行后追加：

```css
@import "./themes/neobrutalism.css";
@import "./themes/dark.css";
@import "./themes/<theme_name>.css";    /* 新增 */
```

### A-4：更新 ThemeSwitcher（主题数 > 2 时必须）

若主题数量超过 2 个，将 `ThemeSwitcher.vue` 从图标切换改为下拉选择器：

```vue
<script setup lang="ts">
import { ref } from "vue";
import { useTheme } from "@/composables/useTheme";

const { themes, currentTheme, setTheme } = useTheme();
const open = ref(false);

function select(name: string) {
  setTheme(name as import("@/themes").ThemeName);
  open.value = false;
}
</script>

<template>
  <div class="relative">
    <button
      class="px-3 py-1.5 border-[length:var(--theme-border-width)] border-[color:var(--theme-border)] bg-card text-card-foreground text-sm font-bold uppercase tracking-wide hover:bg-muted transition-colors"
      @click="open = !open"
    >
      {{ themes.find(t => t.name === currentTheme)?.label ?? currentTheme }}
    </button>

    <div
      v-if="open"
      class="absolute top-full right-0 mt-1 min-w-[140px] bg-card border-[length:var(--theme-border-width)] border-[color:var(--theme-border)] z-50"
      style="box-shadow: var(--theme-shadow-card)"
    >
      <button
        v-for="theme in themes"
        :key="theme.name"
        class="w-full px-4 py-2 text-left text-sm hover:bg-muted transition-colors"
        :class="{ 'text-primary font-bold': currentTheme === theme.name }"
        @click="select(theme.name)"
      >
        {{ theme.label }}
      </button>
    </div>
  </div>
</template>
```

---

## 场景 B — 修改现有主题

### B-1：定位目标文件

```bash
# 查看当前变量值
grep "<variable_name>" <target_dir>/src/themes/<target_theme>.css
```

### B-2：直接编辑 CSS 文件

使用 Edit 工具修改对应变量值。批量修改示例（修改主色 + 对应阴影）：

```css
/* 修改前 */
--theme-primary: #ff2d95;
--theme-shadow-card: 4px 4px 0px #1a1a1a;

/* 修改后 */
--theme-primary: <new_color>;
--theme-shadow-card: 4px 4px 0px <new_shadow_color>;
```

**注意**：`--theme-primary-foreground` 必须与新主色保持足够对比度（WCAG AA 最低 4.5:1）。

---

## 场景 C — 集成到新项目（主题系统不存在）

### C-1：创建目录结构

```bash
mkdir -p <target_dir>/src/themes
mkdir -p <target_dir>/src/stores
mkdir -p <target_dir>/src/composables
```

### C-2：创建核心文件

依次创建以下文件（内容见文末完整代码参考）：

1. `src/themes/index.ts` — ThemeName 类型 + ThemeInfo 列表
2. `src/themes/neobrutalism.css` — 亮色主题变量
3. `src/themes/dark.css` — 暗色主题变量
4. `src/stores/theme.ts` — Pinia store
5. `src/composables/useTheme.ts` — 组合函数
6. `src/components/ThemeSwitcher.vue` — 切换组件

### C-3：配置 app.css

在 `src/app.css` 的顶部添加：

```css
@import "./themes/neobrutalism.css";
@import "./themes/dark.css";

@theme {
  --color-background:        var(--theme-background);
  --color-foreground:        var(--theme-foreground);
  --color-card:              var(--theme-card);
  --color-card-foreground:   var(--theme-card-foreground);
  --color-primary:           var(--theme-primary);
  --color-primary-foreground:var(--theme-primary-foreground);
  --color-secondary:         var(--theme-secondary);
  --color-secondary-foreground: var(--theme-secondary-foreground);
  --color-accent:            var(--theme-accent);
  --color-accent-foreground: var(--theme-accent-foreground);
  --color-destructive:       var(--theme-destructive);
  --color-muted:             var(--theme-muted);
  --color-muted-foreground:  var(--theme-muted-foreground);
  --color-border:            var(--theme-border);
  --color-ring:              var(--theme-ring);
  --color-surface:           var(--theme-surface);
  --radius-theme:            var(--theme-radius);
}
```

### C-4：在 main.ts 中初始化

```typescript
import { createPinia } from "pinia";
import { useThemeStore } from "@/stores/theme";

const app = createApp(App);
app.use(createPinia());

// 在 mount 前初始化主题（读取 localStorage）
const themeStore = useThemeStore();
themeStore.initTheme();

app.mount("#app");
```

---

## 场景 D — 调整 Tailwind Token / 特殊效果

### D-1：新增 Tailwind token

在 `src/app.css` 的 `@theme` 块中添加新映射：

```css
@theme {
  /* 现有 token ... */

  /* 新增示例 */
  --color-glass:    var(--theme-glass);       /* bg-glass */
  --shadow-neon:    var(--theme-shadow-neon); /* shadow-neon */
  --radius-card:    var(--theme-radius);      /* rounded-card */
}
```

同时在每个主题 CSS 中定义对应变量：

```css
[data-theme="<name>"] {
  --theme-glass: rgba(255, 255, 255, 0.1);
  --theme-shadow-neon: 0 0 20px rgba(0, 240, 255, 0.4);
}
```

### D-2：添加主题专属特效

在 `src/app.css` 中用主题选择器保护：

```css
[data-theme="<name>"] .my-effect {
  /* 特效样式 */
}
```

---

## 第 N 步 — 验证

执行以下命令确认修改正确：

```bash
# 1. 确认新主题 CSS 变量完整（应 >= 20 行）
grep -c "^  --theme-" <target_dir>/src/themes/<theme_name>.css

# 2. 确认 app.css 已导入新主题
grep "@import.*themes" <target_dir>/src/app.css

# 3. 确认 index.ts 包含新主题名
grep "ThemeName\|themes\s*=" <target_dir>/src/themes/index.ts

# 4. 语法检查（若项目有 tsc）
cd <target_dir> && npx tsc --noEmit 2>&1 | head -20
```

**验证失败时的处理：**

| 错误现象 | 原因 | 修复 |
|---------|------|------|
| 变量数 < 20 | 有变量未填写 | 对照规范补全缺失变量 |
| `@import` 缺失 | 忘记步骤 A-3 | 在 app.css 追加 import |
| TS 类型错误 | ThemeName 未更新 | 检查 index.ts 联合类型 |
| 切换后样式无变化 | `data-theme` 未正确设置 | 检查 Pinia store 的 `setTheme` 是否更新 `document.documentElement.dataset.theme` |

---

## 参考：完整 CSS 变量规范

每个主题必须定义以下 **22 个**变量（缺失变量会回退到浏览器默认值导致样式异常）：

```
--theme-background        --theme-foreground
--theme-card              --theme-card-foreground
--theme-primary           --theme-primary-foreground
--theme-secondary         --theme-secondary-foreground
--theme-accent            --theme-accent-foreground
--theme-destructive
--theme-muted             --theme-muted-foreground
--theme-border            --theme-ring            --theme-surface
--theme-radius            --theme-border-width
--theme-shadow-card       --theme-shadow-card-hover
--theme-grid
--theme-robot-cyan  --theme-robot-purple  --theme-robot-pink
--theme-robot-green --theme-robot-orange  --theme-robot-yellow
```

## 参考：内置主题完整配色

### Neo-Brutalism（亮色粗粝）

```css
[data-theme="neobrutalism"], :root {
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
```

### Dark（霓虹暗色）

```css
[data-theme="dark"] {
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

## 参考：Dark 主题特殊效果类

```css
[data-theme="dark"] .glass {
  background: rgba(26, 26, 37, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

[data-theme="dark"] .glass-strong {
  background: rgba(37, 37, 50, 0.85);
  backdrop-filter: blur(30px);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

[data-theme="dark"] .neon-glow {
  box-shadow:
    0 0 0 1px rgba(0, 240, 255, 0.3),
    0 0 20px rgba(0, 240, 255, 0.2),
    inset 0 0 20px rgba(0, 240, 255, 0.05);
}

[data-theme="dark"] .gradient-text {
  background: linear-gradient(135deg, #00f0ff, #b829ff, #ff2d95);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

## 参考：状态指示点系统

```css
.status-dot { @apply w-2 h-2 rounded-full; }
.status-running  { background: #00ff88; box-shadow: 0 0 10px #00ff88; animation: pulse 2s ease-in-out infinite; }
.status-idle     { background: #64748b; }
.status-error    { background: var(--theme-destructive); box-shadow: 0 0 10px var(--theme-destructive); animation: pulse 1s ease-in-out infinite; }
.status-connecting { background: #ffee00; box-shadow: 0 0 10px #ffee00; animation: pulse 1.5s ease-in-out infinite; }
```

## 参考：在 JS 中读取 CSS 变量

用于 Canvas 绘图、SVG fill 等需要在 JS 中使用主题颜色的场景：

```typescript
function getRobotColor(robotType: string): string {
  const COLORS = ["cyan", "purple", "pink", "green", "orange", "yellow"];
  const index = robotType.split("").reduce((acc, c) => acc + c.charCodeAt(0), 0) % COLORS.length;
  return getComputedStyle(document.documentElement)
    .getPropertyValue(`--theme-robot-${COLORS[index]}`)
    .trim();
}
```

主题切换时响应式更新：使用 `watch(() => useTheme().currentTheme, () => { /* 重新获取颜色 */ })`。
