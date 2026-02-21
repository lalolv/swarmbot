<script setup lang="ts">
import { computed, ref } from "vue";
import type { RobotState } from "@/stores/observability";

const props = defineProps<{
  robots: RobotState[];
  taskId: string;
}>();

const emit = defineEmits<{
  "focus-robot": [robotType: string];
}>();

// 面板折叠状态
const collapsed = ref(false);

// 颜色 palette（复用 RobotCard 的逻辑）
const PALETTE_VARS = [
  "--theme-robot-cyan",
  "--theme-robot-purple",
  "--theme-robot-pink",
  "--theme-robot-green",
  "--theme-robot-orange",
  "--theme-robot-yellow",
];

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

function getRobotColor(robotType: string): string {
  const idx = hashString(robotType) % PALETTE_VARS.length;
  return getComputedStyle(document.documentElement)
    .getPropertyValue(PALETTE_VARS[idx])
    .trim();
}

function getStateDotClass(state: string): string {
  switch (state) {
    case "running": return "status-running";
    case "error": return "status-error";
    case "idle": return "status-idle";
    default: return "status-idle";
  }
}

function focusRobot(robotType: string) {
  emit("focus-robot", robotType);
}
</script>

<template>
  <!-- 无机器人时整体隐藏 -->
  <template v-if="robots.length > 0">
    <!-- 折叠时只显示 tab -->
    <div
      v-if="collapsed"
      class="fixed right-0 top-1/3 z-40 cursor-pointer"
      @click="collapsed = false"
    >
      <div
        class="flex flex-col items-center justify-center gap-1.5 px-2 py-4 bg-card border-(length:--theme-border-width) border-r-0 border-border rounded-l-(--theme-radius) shadow-card hover:shadow-card-hover transition-all"
      >
        <svg class="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
        <span
          class="text-[10px] font-display font-semibold text-muted-foreground uppercase tracking-wider"
          style="writing-mode: vertical-rl; text-orientation: mixed;"
        >机器人</span>
        <svg class="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </div>
    </div>

    <!-- 展开面板 -->
    <Transition name="panel-right">
      <div
        v-if="!collapsed"
        class="fixed right-4 top-20 z-40 w-60 flex flex-col bg-card/95 backdrop-blur border-(length:--theme-border-width) border-border rounded-(--theme-radius) shadow-card-hover overflow-hidden max-h-[calc(100vh-6.5rem)]"
      >
        <!-- Panel Header -->
        <div class="flex items-center gap-2 px-4 py-3 border-b border-border shrink-0">
          <!-- 折叠按钮 -->
          <button
            @click="collapsed = true"
            class="p-1 rounded text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            title="收起"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          <svg class="w-4 h-4 text-primary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <span class="flex-1 text-xs font-display font-semibold text-foreground uppercase tracking-wider">机器人</span>
          <span class="text-[10px] font-mono text-muted-foreground">{{ robots.length }}</span>
        </div>

        <!-- Robot List -->
        <div class="flex-1 min-h-0 overflow-y-auto">
          <button
            v-for="robot in robots"
            :key="robot.robot_type"
            @click="focusRobot(robot.robot_type)"
            class="w-full px-4 py-3 text-left hover:bg-muted transition-colors group flex items-center gap-3"
            title="点击定位到此机器人"
          >
            <!-- Color dot -->
            <div
              class="w-2.5 h-2.5 rounded-full shrink-0 ring-1 ring-border"
              :style="{ backgroundColor: getRobotColor(robot.robot_type) }"
            ></div>

            <!-- Info -->
            <div class="flex-1 min-w-0">
              <div class="text-sm font-semibold text-foreground truncate leading-tight">
                {{ robot.robot_type }}
              </div>
              <div class="flex items-center gap-1.5 mt-0.5">
                <span class="status-dot" :class="getStateDotClass(robot.state)"></span>
                <span class="text-[10px] text-muted-foreground">{{ robot.state }}</span>
              </div>
            </div>

            <!-- Signal counts -->
            <div class="flex flex-col items-end gap-0.5 shrink-0">
              <span class="text-[10px] font-mono" :style="{ color: getRobotColor(robot.robot_type) }">
                ↑{{ robot.signals_in || 0 }}
              </span>
              <span class="text-[10px] font-mono text-muted-foreground opacity-60">
                ↓{{ robot.signals_out || 0 }}
              </span>
            </div>

            <!-- Focus icon (hover) -->
            <svg
              class="w-3.5 h-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </button>
        </div>

        <!-- Hint -->
        <div class="px-4 py-2 border-t border-border shrink-0">
          <p class="text-[10px] text-muted-foreground text-center">点击机器人以在画布中定位</p>
        </div>
      </div>
    </Transition>
  </template>
</template>

<style scoped>
.panel-right-enter-active,
.panel-right-leave-active {
  transition: all 0.25s ease;
}
.panel-right-enter-from,
.panel-right-leave-to {
  opacity: 0;
  transform: translateX(16px);
}
</style>
