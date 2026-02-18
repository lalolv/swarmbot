---
name: create-vue-frontend
description: Generate a Vue 3 + Vite + Tailwind CSS 4 frontend scaffold with infinite canvas, header bar, task management, SSE real-time subscription, and a dual-theme (Neo-Brutalism / Dark) design system. Use when the user asks to create or scaffold a Vue 3 frontend for a robot observability system, task dashboard, real-time monitoring UI, or similar data-driven application.
---

# Create Vue Frontend

为机器人任务系统生成完整的 Vue 3 + Vite 前端脚手架（36 个文件）。

## 必要输入

收集并确认以下参数（有默认值）：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `app_name` | 显示在标题栏的应用名称 | `My App` |
| `app_subtitle` | 副标题文字 | `Task Orchestration System` |
| `api_port` | 后端 API 端口（用于 Vite proxy） | `8000` |
| `target_dir` | 前端目录路径 | `frontend` |
| `package_name` | npm 包名（小写+连字符） | `my-app-frontend` |

## 参数校验

- `app_name`：仅含字母数字空格连字符下划线
- `api_port`：2~5 位纯数字
- `package_name`：符合 npm 规范（`^[a-z0-9][a-z0-9\-]*$`）
- `target_dir`：不能是根目录，不能越出工作区

## 执行流程

**第 1 步 — 运行生成脚本：**

```bash
python3 .claude/skills/create-vue-frontend/scripts/generate.py \
  --app-name "<app_name>" \
  --app-subtitle "<app_subtitle>" \
  --api-port <api_port> \
  --target-dir <target_dir> \
  --package-name <package_name>
```

**第 2 步 — 运行校验脚本：**

```bash
python3 .claude/skills/create-vue-frontend/scripts/validate_generated.py \
  --root <target_dir>
```

若校验失败，修复报告的问题后重新运行校验。

**第 3 步 — 安装依赖并启动：**

```bash
cd <target_dir> && npm install && npm run dev
```

## 生成内容

脚本按以下顺序生成 36 个文件：

**配置层**：`package.json` / `vite.config.ts` / `tsconfig.json` / `tsconfig.node.json` / `index.html`

**主题系统**：`src/themes/index.ts` / `neobrutalism.css` / `dark.css` / `src/app.css`

**核心层**：`src/main.ts` / `src/lib/utils.ts` / `src/stores/theme.ts` / `src/stores/observability.ts` / `src/composables/useTheme.ts` / `src/api/client.ts`

**UI 组件库**：Button / Badge / Dialog / Input / Alert / Card（各含 `.vue` + `index.ts`）

**业务组件**：`ThemeSwitcher.vue` / `Header.vue` / `InfiniteCanvas.vue` / `RobotCard.vue` / `RobotAvatar.vue`

**根组件**：`src/App.vue`

## 架构说明

- **主题**：CSS 变量 + `data-theme` 属性切换，Neo-Brutalism（粗边框/硬阴影）与 Dark（霓虹发光）双主题
- **无限画布**：鼠标拖拽平移 + 滚轮缩放（0.3×~3×）+ Fit All + Reset Layout
- **SSE**：`observability` store 管理 EventSource 连接，处理 7 种事件类型
- **机器人卡片**：6 色轮换，支持 data_update 进度条 / process_result 转换流 / 通用 KV 可视化
- **机器人头像**：SVG 动画，5 种表情（neutral/receiving/sending/happy/error）+ 天线状态灯

## 扩展

- **新主题**：参考 `apply-frontend-theme` skill
- **新信号类型**：修改 `src/components/RobotCard.vue.tpl` 中的信号展示区
- **新 API 端点**：修改 `src/api/client.ts.tpl` + `src/stores/observability.ts.tpl`
