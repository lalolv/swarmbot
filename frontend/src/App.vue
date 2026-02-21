<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

import Header from "./components/Header.vue";
import InfiniteCanvas from "./components/InfiniteCanvas.vue";
import TaskListPanel from "./components/TaskListPanel.vue";
import RobotListPanel from "./components/RobotListPanel.vue";
import { Alert } from "./components/ui/alert";
import { useObservabilityStore } from "./stores/observability";
import { useTheme } from "./composables/useTheme";

const store = useObservabilityStore();
const { isDark } = useTheme();

// 画布 ref，用于调用 focusRobot
const canvasRef = ref<InstanceType<typeof InfiniteCanvas> | null>(null);

// Methods
async function handleCreateTask(form: any) {
  await store.createNewTask(form);
}

async function handleSelectTask(taskId: string) {
  // 选择即订阅；startMonitoring 内部会先 stopMonitoring 取消上一个订阅
  await store.startMonitoring(taskId);
}

async function handleDeleteTask(taskId: string) {
  await store.cleanupTask(taskId);
  canvasRef.value?.clearTaskPositions(taskId);
}

async function handleSleepTask(taskId: string) {
  await store.sleepTask(taskId);
}

async function handleWakeTask(taskId: string) {
  await store.wakeTask(taskId);
}

async function handleRefreshTasks() {
  await store.refreshTasks();
}

function handleFocusRobot(robotType: string) {
  canvasRef.value?.focusRobot(robotType);
}

// Lifecycle
onMounted(() => {
  store.initialize();
});

onBeforeUnmount(() => {
  store.stopMonitoring();
});
</script>

<template>
  <div class="relative w-full h-full overflow-hidden bg-background">
    <!-- Neon Dark 背景效果 -->
    <div v-if="isDark" class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-1/4 -left-1/4 w-[800px] h-[800px] rounded-full bg-primary/5 blur-[150px]"></div>
      <div class="absolute -bottom-1/4 -right-1/4 w-[600px] h-[600px] rounded-full bg-secondary/5 blur-[120px]"></div>
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] rounded-full bg-accent/3 blur-[200px]"></div>
      <div class="absolute inset-0 opacity-30"
           style="background-image: linear-gradient(rgba(0, 240, 255, 0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 240, 255, 0.02) 1px, transparent 1px); background-size: 100px 100px;">
      </div>
    </div>

    <!-- Header（只保留 Logo + 主题切换） -->
    <Header />

    <!-- Main Content（无限画布） -->
    <main class="absolute inset-0 pt-16">
      <InfiniteCanvas
        ref="canvasRef"
        :robots="store.robotList"
        :task-id="store.monitorTaskId"
        :task-state="store.taskState"
      />
    </main>

    <!-- 左侧：任务列表面板 -->
    <TaskListPanel
      :tasks="store.tasks"
      :robot-types="store.robotTypes"
      :current-task-id="store.monitorTaskId"
      @create-task="handleCreateTask"
      @select-task="handleSelectTask"
      @delete-task="handleDeleteTask"
      @sleep-task="handleSleepTask"
      @wake-task="handleWakeTask"
      @refresh-tasks="handleRefreshTasks"
    />

    <!-- 右侧：机器人列表面板 -->
    <RobotListPanel
      :robots="store.robotList"
      :task-id="store.monitorTaskId"
      @focus-robot="handleFocusRobot"
    />

    <!-- Toast Notification -->
    <Transition name="toast">
      <Alert
        v-if="store.lastError"
        variant="destructive"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 max-w-md"
      >
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="text-sm flex-1">{{ store.lastError }}</span>
        <button @click="store.lastError = ''" class="ml-2 opacity-60 hover:opacity-100">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </Alert>
    </Transition>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
</style>
