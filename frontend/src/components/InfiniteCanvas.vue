<script setup lang="ts">
import { computed, ref, watch } from "vue";
import RobotCard from "./RobotCard.vue";
import { Button } from "@/components/ui/button";
import type { RobotState } from "@/stores/observability";

defineOptions({ name: "InfiniteCanvas" });

interface DisplayRobot extends RobotState {
  position: { x: number; y: number };
}

const props = defineProps<{
  robots: RobotState[];
  taskId: string;
  taskState: string;
}>();

// ===== Per-task position persistence =====

// Session-level cache: survives reactive re-renders within a page session
const taskPositionCache = new Map<string, Map<string, { x: number; y: number }>>();

function loadPositionsForTask(taskId: string): Map<string, { x: number; y: number }> {
  if (taskPositionCache.has(taskId)) {
    return taskPositionCache.get(taskId)!;
  }
  try {
    const raw = localStorage.getItem(`robot-positions:${taskId}`);
    if (raw) {
      const parsed = JSON.parse(raw) as Record<string, { x: number; y: number }>;
      const map = new Map(Object.entries(parsed));
      taskPositionCache.set(taskId, map);
      return map;
    }
  } catch { /* ignore */ }
  const newMap = new Map<string, { x: number; y: number }>();
  taskPositionCache.set(taskId, newMap);
  return newMap;
}

function savePositionsForTask(taskId: string, positions: Map<string, { x: number; y: number }>) {
  taskPositionCache.set(taskId, positions);
  try {
    localStorage.setItem(`robot-positions:${taskId}`, JSON.stringify(Object.fromEntries(positions)));
  } catch { /* ignore quota errors */ }
}

// ===== Canvas state =====

const canvasRef = ref<HTMLDivElement | null>(null);
const transform = ref({ x: 0, y: 0, scale: 1 });
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const isAnimating = ref(false);

// Robot positions for current task
const robotPositions = ref(new Map<string, { x: number; y: number }>());

function initializeRobotPositions() {
  const newRobots = props.robots;
  const existingIds = new Set(robotPositions.value.keys());
  const newIds = new Set(newRobots.map((r) => r.robot_type));

  for (const id of existingIds) {
    if (!newIds.has(id)) {
      robotPositions.value.delete(id);
    }
  }

  const unpositioned = newRobots.filter(
    (r) => !robotPositions.value.has(r.robot_type)
  );
  if (unpositioned.length > 0) {
    const cols = Math.ceil(Math.sqrt(unpositioned.length));
    const cardWidth = 340;
    const cardHeight = 240;
    const gap = 40;

    unpositioned.forEach((robot, index) => {
      const col = index % cols;
      const row = Math.floor(index / cols);
      const x = (col - (cols - 1) / 2) * (cardWidth + gap);
      const y =
        (row - Math.floor((unpositioned.length - 1) / cols) / 2) *
        (cardHeight + gap);
      robotPositions.value.set(robot.robot_type, { x, y });
    });
  }
}

// Watch taskId FIRST so positions map is swapped before robots watcher runs
watch(
  () => props.taskId,
  (newTaskId, oldTaskId) => {
    if (oldTaskId) {
      savePositionsForTask(oldTaskId, robotPositions.value);
    }
    robotPositions.value = newTaskId ? loadPositionsForTask(newTaskId) : new Map();
  },
  { immediate: true }
);

watch(
  () => props.robots,
  () => {
    initializeRobotPositions();
  },
  { immediate: true, deep: true }
);

const displayRobots = computed<DisplayRobot[]>(() => {
  return props.robots.map((robot) => ({
    ...robot,
    position: robotPositions.value.get(robot.robot_type) || { x: 0, y: 0 },
  }));
});

const motionMode = computed<"full" | "reduced" | "off">(() => {
  const count = displayRobots.value.length;
  if (count >= 60) {
    return "off";
  }
  if (count >= 24) {
    return "reduced";
  }
  return "full";
});

// Methods
function onMouseDown(e: MouseEvent) {
  if (
    (e.target as HTMLElement).closest(".robot-card") ||
    (e.target as HTMLElement).closest("button")
  ) {
    return;
  }
  isDragging.value = true;
  dragStart.value = {
    x: e.clientX - transform.value.x,
    y: e.clientY - transform.value.y,
  };
  canvasRef.value!.style.cursor = "grabbing";
}

function onMouseMove(e: MouseEvent) {
  if (isDragging.value) {
    transform.value.x = e.clientX - dragStart.value.x;
    transform.value.y = e.clientY - dragStart.value.y;
  }
}

function onMouseUp() {
  isDragging.value = false;
  if (canvasRef.value) {
    canvasRef.value.style.cursor = "grab";
  }
}

function onWheel(e: WheelEvent) {
  e.preventDefault();
  const delta = e.deltaY > 0 ? 0.9 : 1.1;
  const newScale = Math.max(
    0.3,
    Math.min(3, transform.value.scale * delta)
  );

  const rect = canvasRef.value!.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;

  const scaleRatio = newScale / transform.value.scale;
  transform.value.x = mouseX - (mouseX - transform.value.x) * scaleRatio;
  transform.value.y = mouseY - (mouseY - transform.value.y) * scaleRatio;
  transform.value.scale = newScale;
}

function onRobotMove(robotType: string, deltaX: number, deltaY: number) {
  const current = robotPositions.value.get(robotType);
  if (current) {
    robotPositions.value.set(robotType, {
      x: current.x + deltaX / transform.value.scale,
      y: current.y + deltaY / transform.value.scale,
    });
  }
}

function onRobotMoveEnd() {
  if (props.taskId) {
    savePositionsForTask(props.taskId, robotPositions.value);
  }
}

function animateTransform(newTransform: {
  x: number;
  y: number;
  scale: number;
}) {
  isAnimating.value = true;
  Object.assign(transform.value, newTransform);
  setTimeout(() => {
    isAnimating.value = false;
  }, 300);
}

function fitAll() {
  if (props.robots.length === 0) return;

  let minX = Infinity,
    maxX = -Infinity,
    minY = Infinity,
    maxY = -Infinity;
  let hasValidPositions = false;

  for (const [, pos] of robotPositions.value) {
    hasValidPositions = true;
    minX = Math.min(minX, pos.x - 170);
    maxX = Math.max(maxX, pos.x + 170);
    minY = Math.min(minY, pos.y - 120);
    maxY = Math.max(maxY, pos.y + 120);
  }

  if (!hasValidPositions) return;

  const rect = canvasRef.value?.getBoundingClientRect();
  if (!rect) return;

  const contentW = maxX - minX;
  const contentH = maxY - minY;
  const padding = 60;

  const scaleX = (rect.width - padding * 2) / contentW;
  const scaleY = (rect.height - padding * 2) / contentH;
  const scale = Math.max(0.3, Math.min(3, Math.min(scaleX, scaleY, 1)));

  const avgX = (minX + maxX) / 2;
  const avgY = (minY + maxY) / 2;

  animateTransform({
    x: rect.width / 2 - (rect.width / 2 + avgX) * scale,
    y: rect.height / 2 - (rect.height / 2 + avgY) * scale,
    scale,
  });
}

function resetLayout() {
  robotPositions.value.clear();
  initializeRobotPositions();
  animateTransform({ x: 0, y: 0, scale: 1 });
  if (props.taskId) {
    savePositionsForTask(props.taskId, robotPositions.value);
  }
}

// 定位到指定机器人（由外部面板调用）
// 机器人卡片坐标系：left = 50% + pos.x，top = 50% + pos.y
// 与 fitAll 保持一致：tx = W/2 - (W/2 + pos.x) * scale
function focusRobot(robotType: string) {
  const pos = robotPositions.value.get(robotType);
  if (!pos || !canvasRef.value) return;

  const rect = canvasRef.value.getBoundingClientRect();
  const scale = Math.max(0.5, Math.min(1.5, transform.value.scale));
  animateTransform({
    x: rect.width / 2 - (rect.width / 2 + pos.x) * scale,
    y: rect.height / 2 - (rect.height / 2 + pos.y) * scale,
    scale,
  });
}

function clearTaskPositions(taskId: string) {
  taskPositionCache.delete(taskId);
  try {
    localStorage.removeItem(`robot-positions:${taskId}`);
  } catch { /* ignore */ }
}

defineExpose({ focusRobot, clearTaskPositions });
</script>

<template>
  <div
    ref="canvasRef"
    class="absolute inset-0 overflow-hidden cursor-grab bg-background"
    :class="{ 'canvas-grid': true }"
    @mousedown="onMouseDown"
    @mousemove="onMouseMove"
    @mouseup="onMouseUp"
    @mouseleave="onMouseUp"
    @wheel="onWheel"
  >
    <!-- Transform container -->
    <div
      class="absolute inset-0"
      :class="{ 'transition-transform duration-300 ease-out': isAnimating }"
      :style="{
        transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
        transformOrigin: '0 0',
      }"
    >
      <!-- Robot Cards -->
      <RobotCard
        v-for="robot in displayRobots"
        :key="robot.robot_type"
        :robot="robot"
        :scale="transform.scale"
        :motion-mode="motionMode"
        @move="(dx: number, dy: number) => onRobotMove(robot.robot_type, dx, dy)"
        @move-end="onRobotMoveEnd"
      />

      <!-- Empty State -->
      <div
        v-if="robots.length === 0"
        class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none"
      >
        <div class="mb-6">
          <svg class="w-24 h-24 mx-auto text-muted-foreground/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1"
              d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        </div>
        <h3 class="font-display text-2xl font-bold text-muted-foreground mb-2">
          {{ taskId ? '暂无机器人' : '未选择任务' }}
        </h3>
        <p class="text-muted-foreground max-w-sm mx-auto">
          {{
            taskId
              ? '该任务尚未启动或没有分配机器人。创建任务并开始监控以查看机器人状态。'
              : '请从顶部菜单选择一个任务或创建新任务开始。'
          }}
        </p>
      </div>
    </div>

    <!-- Controls -->
    <div class="absolute bottom-6 right-6 flex flex-col gap-2">
      <Button
        variant="outline"
        size="icon"
        @click="fitAll"
        :disabled="robots.length === 0"
        title="适配全部"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
        </svg>
      </Button>
      <Button
        variant="outline"
        size="icon"
        @click="resetLayout"
        :disabled="robots.length === 0"
        title="重置布局"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </Button>
    </div>

    <!-- Zoom level indicator -->
    <div class="absolute bottom-6 left-6 px-3 py-1.5 rounded-(--theme-radius) bg-card border-(length:--theme-border-width) border-border shadow-card text-xs font-mono font-bold text-foreground">
      {{ Math.round(transform.scale * 100) }}%
    </div>
  </div>
</template>
