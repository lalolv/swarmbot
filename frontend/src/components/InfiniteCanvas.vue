<script setup>
import { computed, ref, watch } from "vue";
import RobotCard from "./RobotCard.vue";

const props = defineProps({
  robots: {
    type: Array,
    default: () => [],
  },
  taskId: {
    type: String,
    default: "",
  },
  taskState: {
    type: String,
    default: "idle",
  },
});

// Canvas state
const canvasRef = ref(null);
const transform = ref({ x: 0, y: 0, scale: 1 });
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const canvasSize = ref({ width: 0, height: 0 });

// Robot positions (persisted during session)
const robotPositions = ref(new Map());

function initializeRobotPositions() {
  const newRobots = props.robots;
  const existingIds = new Set(robotPositions.value.keys());
  const newIds = new Set(newRobots.map(r => r.robot_type));
  
  for (const id of existingIds) {
    if (!newIds.has(id)) {
      robotPositions.value.delete(id);
    }
  }
  
  const unpositioned = newRobots.filter(r => !robotPositions.value.has(r.robot_type));
  if (unpositioned.length > 0) {
    const cols = Math.ceil(Math.sqrt(unpositioned.length));
    const cardWidth = 340;
    const cardHeight = 240;
    const gap = 40;
    
    unpositioned.forEach((robot, index) => {
      const col = index % cols;
      const row = Math.floor(index / cols);
      const x = (col - (cols - 1) / 2) * (cardWidth + gap);
      const y = (row - Math.floor((unpositioned.length - 1) / cols) / 2) * (cardHeight + gap);
      robotPositions.value.set(robot.robot_type, { x, y });
    });
  }
}

// Initialize robot positions
watch(() => props.robots, () => {
  initializeRobotPositions();
}, { immediate: true, deep: true });

// Computed
const displayRobots = computed(() => {
  return props.robots.map(robot => ({
    ...robot,
    position: robotPositions.value.get(robot.robot_type) || { x: 0, y: 0 },
  }));
});

// Methods
function onMouseDown(e) {
  // Don't start dragging if clicking on a robot card or button
  if (e.target.closest('.card-robot') || e.target.closest('button')) {
    return;
  }
  isDragging.value = true;
  dragStart.value = { 
    x: e.clientX - transform.value.x, 
    y: e.clientY - transform.value.y 
  };
  canvasRef.value.style.cursor = 'grabbing';
}

function onMouseMove(e) {
  if (isDragging.value) {
    transform.value.x = e.clientX - dragStart.value.x;
    transform.value.y = e.clientY - dragStart.value.y;
  }
}

function onMouseUp() {
  isDragging.value = false;
  if (canvasRef.value) {
    canvasRef.value.style.cursor = 'grab';
  }
}

function onWheel(e) {
  e.preventDefault();
  const delta = e.deltaY > 0 ? 0.9 : 1.1;
  const newScale = Math.max(0.3, Math.min(3, transform.value.scale * delta));
  
  // Zoom towards mouse position
  const rect = canvasRef.value.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  
  const scaleRatio = newScale / transform.value.scale;
  transform.value.x = mouseX - (mouseX - transform.value.x) * scaleRatio;
  transform.value.y = mouseY - (mouseY - transform.value.y) * scaleRatio;
  transform.value.scale = newScale;
}

function onRobotMove(robotType, deltaX, deltaY) {
  const current = robotPositions.value.get(robotType);
  if (current) {
    robotPositions.value.set(robotType, {
      x: current.x + deltaX / transform.value.scale,
      y: current.y + deltaY / transform.value.scale,
    });
  }
}

function resetView() {
  transform.value = { x: 0, y: 0, scale: 1 };
}

function centerRobots() {
  if (props.robots.length === 0) return;
  
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  let hasValidPositions = false;
  
  for (const [_, pos] of robotPositions.value) {
    hasValidPositions = true;
    minX = Math.min(minX, pos.x);
    maxX = Math.max(maxX, pos.x + 340);
    minY = Math.min(minY, pos.y);
    maxY = Math.max(maxY, pos.y + 240);
  }
  
  if (!hasValidPositions) return;
  
  const robotsCenterX = (minX + maxX) / 2;
  const robotsCenterY = (minY + maxY) / 2;
  const rect = canvasRef.value?.getBoundingClientRect();
  if (rect) {
    // Center the robots on screen: translate so robot center aligns with canvas center
    transform.value.x = rect.width / 2 - robotsCenterX * transform.value.scale;
    transform.value.y = rect.height / 2 - robotsCenterY * transform.value.scale;
  }
}
</script>

<template>
  <div 
    ref="canvasRef"
    class="absolute inset-0 overflow-hidden cursor-grab canvas-grid"
    @mousedown="onMouseDown"
    @mousemove="onMouseMove"
    @mouseup="onMouseUp"
    @mouseleave="onMouseUp"
    @wheel="onWheel"
  >
    <!-- Transform container -->
    <div 
      class="absolute inset-0"
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
        @move="(dx, dy) => onRobotMove(robot.robot_type, dx, dy)"
      />

      <!-- Empty State -->
      <div v-if="robots.length === 0" 
           class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
        <div class="empty-state-icon mb-6">
          <svg class="w-24 h-24 mx-auto text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" 
              d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        </div>
        <h3 class="font-display text-2xl font-semibold text-slate-400 mb-2">
          {{ taskId ? '暂无机器人' : '未选择任务' }}
        </h3>
        <p class="text-slate-500 max-w-sm mx-auto">
          {{ taskId 
            ? '该任务尚未启动或没有分配机器人。创建任务并开始监控以查看机器人状态。' 
            : '请从顶部菜单选择一个任务或创建新任务开始。' 
          }}
        </p>
      </div>
    </div>

    <!-- Controls -->
    <div class="absolute bottom-6 right-6 flex flex-col gap-2">
      <button
        @click="resetView"
        class="w-10 h-10 rounded-xl glass flex items-center justify-center text-slate-400 hover:text-white hover:border-neon-cyan/30 transition-all"
        title="重置视图"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
      <button
        @click="centerRobots"
        class="w-10 h-10 rounded-xl glass flex items-center justify-center text-slate-400 hover:text-white hover:border-neon-cyan/30 transition-all"
        title="居中机器人"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
            d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
        </svg>
      </button>
    </div>

    <!-- Zoom level indicator -->
    <div class="absolute bottom-6 left-6 px-3 py-1.5 rounded-lg glass text-xs font-mono text-slate-400">
      {{ Math.round(transform.scale * 100) }}%
    </div>
  </div>
</template>

<style scoped>
.canvas-grid {
  background: 
    radial-gradient(ellipse at center, rgba(0, 240, 255, 0.02) 0%, transparent 70%),
    var(--void);
}
</style>
