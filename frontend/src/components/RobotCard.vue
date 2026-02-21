<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import RobotAvatar from "./RobotAvatar.vue";
import type { Expression } from "./RobotAvatar.vue";
import { Card } from "@/components/ui/card";
import type { RobotState } from "@/stores/observability";
import { useThemeStore } from "@/stores/theme";

interface RobotWithPosition extends RobotState {
  position: { x: number; y: number };
}

const props = defineProps<{
  robot: RobotWithPosition;
  scale: number;
  motionMode?: "full" | "reduced" | "off";
}>();

const emit = defineEmits<{
  move: [dx: number, dy: number];
  "move-end": [];
}>();

// --- 色板（通过 CSS 变量适配明暗主题） ---
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

const themeStore = useThemeStore();

const colorVar = computed(() => {
  const idx = hashString(props.robot.robot_type) % PALETTE_VARS.length;
  return PALETTE_VARS[idx];
});

const colorHex = computed(() => {
  // 依赖 themeStore.colorScheme 使主题切换时自动重新计算
  void themeStore.colorScheme;
  return getComputedStyle(document.documentElement)
    .getPropertyValue(colorVar.value)
    .trim();
});

// --- 拖拽 ---
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });

function onMouseDown(e: MouseEvent) {
  e.stopPropagation();
  isDragging.value = true;
  dragStart.value = { x: e.clientX, y: e.clientY };
  document.addEventListener("mousemove", onMouseMove);
  document.addEventListener("mouseup", onMouseUp);
}

function onMouseMove(e: MouseEvent) {
  if (!isDragging.value) return;
  const deltaX = e.clientX - dragStart.value.x;
  const deltaY = e.clientY - dragStart.value.y;
  emit("move", deltaX, deltaY);
  dragStart.value = { x: e.clientX, y: e.clientY };
}

function onMouseUp() {
  if (!isDragging.value) return;
  isDragging.value = false;
  document.removeEventListener("mousemove", onMouseMove);
  document.removeEventListener("mouseup", onMouseUp);
  emit("move-end");
}

// --- 时间 ---
const formattedTime = computed(() => {
  if (!props.robot.updated_at) return "-";
  const date = new Date(props.robot.updated_at);
  return date.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
});

// --- 信号 ---
const latestSignal = computed(() => props.robot.latest_signal || null);
const signalType = computed(() => latestSignal.value?.type || null);
const signalData = computed(
  () => latestSignal.value?.data as Record<string, any> | null
);

// data_update 可视化
const dataUpdateViz = computed(() => {
  if (signalType.value !== "data_update" || !signalData.value) return null;
  const { value, min_value, max_value } = signalData.value;
  if (value == null || min_value == null || max_value == null) return null;
  const range = max_value - min_value;
  const pct = range > 0 ? ((value - min_value) / range) * 100 : 0;
  return {
    value,
    min: min_value,
    max: max_value,
    pct: Math.max(0, Math.min(100, pct)),
  };
});

// process_result 可视化
const processResultViz = computed(() => {
  if (signalType.value !== "process_result" || !signalData.value) return null;
  const { input_value, coefficient, offset, result_value } = signalData.value;
  if (input_value == null || result_value == null) return null;
  return {
    input: input_value,
    coeff: coefficient,
    offset,
    result: result_value,
  };
});

// 通用 key-value fallback
const genericEntries = computed(() => {
  if (!signalData.value || dataUpdateViz.value || processResultViz.value)
    return null;
  const entries = Object.entries(signalData.value).filter(
    ([k]) => k !== "timestamp" && k !== "source_type"
  );
  return entries.length > 0 ? entries : null;
});

// --- 表情动画 ---
const expression = ref<Expression>("neutral");
let expressionTimer: ReturnType<typeof setTimeout> | null = null;
let expressionFollowupTimer: ReturnType<typeof setTimeout> | null = null;
let lastExpressionAt = 0;

const isMotionReduced = computed(() => props.motionMode === "reduced");
const isMotionOff = computed(() => props.motionMode === "off");

function clearExpressionTimers() {
  if (expressionTimer) {
    clearTimeout(expressionTimer);
    expressionTimer = null;
  }
  if (expressionFollowupTimer) {
    clearTimeout(expressionFollowupTimer);
    expressionFollowupTimer = null;
  }
}

function canTriggerAnimatedExpression(): boolean {
  if (props.robot.state === "error" || isMotionOff.value) {
    return false;
  }

  const now = Date.now();
  const throttleMs = isMotionReduced.value ? 900 : 450;
  if (now - lastExpressionAt < throttleMs) {
    return false;
  }

  lastExpressionAt = now;
  return true;
}

function setTempExpression(expr: Expression, duration = 1500) {
  if (isMotionOff.value) {
    return;
  }
  if (expressionTimer) clearTimeout(expressionTimer);
  expression.value = expr;
  expressionTimer = setTimeout(() => {
    // 回到 neutral，但 error 状态由下面的 watch 控制
    if (props.robot.state !== "error") {
      expression.value = "neutral";
    }
    expressionTimer = null;
  }, duration);
}

// error 状态始终强制 error 表情
watch(
  () => props.robot.state,
  (state) => {
    if (state === "error") {
      clearExpressionTimers();
      expression.value = "error";
    } else if (expression.value === "error") {
      expression.value = "neutral";
    }
  },
  { immediate: true }
);

// 监听 signals_in 变化 → receiving → 短暂 happy
watch(
  () => props.robot.signals_in,
  (newVal, oldVal) => {
    if (oldVal != null && newVal !== oldVal && canTriggerAnimatedExpression()) {
      const duration = isMotionReduced.value ? 700 : 1200;
      setTempExpression("receiving", duration);
      if (!isMotionReduced.value) {
        expressionFollowupTimer = setTimeout(() => {
          if (props.robot.state !== "error" && expression.value === "receiving") {
            setTempExpression("happy", 800);
          }
          expressionFollowupTimer = null;
        }, duration);
      }
    }
  }
);

// 监听 signals_out 变化 → sending → 短暂 happy
watch(
  () => props.robot.signals_out,
  (newVal, oldVal) => {
    if (oldVal != null && newVal !== oldVal && canTriggerAnimatedExpression()) {
      const duration = isMotionReduced.value ? 700 : 1200;
      setTempExpression("sending", duration);
      if (!isMotionReduced.value) {
        expressionFollowupTimer = setTimeout(() => {
          if (props.robot.state !== "error" && expression.value === "sending") {
            setTempExpression("happy", 800);
          }
          expressionFollowupTimer = null;
        }, duration);
      }
    }
  }
);

watch(
  () => props.motionMode,
  (mode) => {
    if (mode === "off" && props.robot.state !== "error") {
      clearExpressionTimers();
      expression.value = "neutral";
    }
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  clearExpressionTimers();
});
</script>

<template>
  <Card
    class="robot-card absolute w-[340px] p-4 cursor-move select-none"
    :class="{ 'dragging': isDragging }"
    :style="{
      left: `calc(50% + ${robot.position.x}px)`,
      top: `calc(50% + ${robot.position.y}px)`,
      transform: 'translate(-50%, -50%)',
      '--robot-color': colorHex,
    }"
    @mousedown="onMouseDown"
  >
    <!-- Header -->
    <div class="flex items-center gap-3 mb-3">
      <RobotAvatar
        :color="colorHex"
        :color-scheme="themeStore.colorScheme"
        :motion-mode="props.motionMode || 'full'"
        :state="robot.state"
        :uid="robot.robot_type"
        :expression="expression"
      />

      <div class="flex-1 min-w-0">
        <h4 class="font-display font-bold text-foreground text-sm truncate">
          {{ robot.robot_type }}
        </h4>
        <div class="flex items-center gap-3 mt-0.5">
          <span class="signal-count" :style="{ color: colorHex }">
            <svg class="w-3 h-3 inline-block mr-0.5" viewBox="0 0 12 12" fill="currentColor">
              <path d="M6 2L9 6H3L6 2Z" />
            </svg>
            {{ robot.signals_in || 0 }}
          </span>
          <span class="signal-count" :style="{ color: colorHex, opacity: 0.65 }">
            <svg class="w-3 h-3 inline-block mr-0.5" viewBox="0 0 12 12" fill="currentColor">
              <path d="M6 10L3 6H9L6 10Z" />
            </svg>
            {{ robot.signals_out || 0 }}
          </span>
        </div>
      </div>
    </div>

    <!-- Latest Signal -->
    <div v-if="latestSignal" class="signal-section">
      <div class="section-label">Latest Signal</div>

      <!-- data_update 进度条可视化 -->
      <div v-if="dataUpdateViz" class="signal-viz">
        <div class="flex items-end justify-between mb-2">
          <span class="text-[10px] font-mono text-muted-foreground uppercase">data_update</span>
          <span class="text-xl font-mono font-bold" :style="{ color: colorHex }">
            {{ dataUpdateViz.value.toFixed(2) }}
          </span>
        </div>
        <div class="progress-track">
          <div
            class="progress-bar"
            :style="{
              width: dataUpdateViz.pct + '%',
              backgroundColor: colorHex,
              boxShadow: `0 0 8px ${colorHex}40`,
            }"
          ></div>
        </div>
        <div class="flex justify-between mt-1">
          <span class="text-[9px] font-mono text-muted-foreground">{{ dataUpdateViz.min }}</span>
          <span class="text-[9px] font-mono text-muted-foreground">{{ dataUpdateViz.max }}</span>
        </div>
      </div>

      <!-- process_result 转换流程可视化 -->
      <div v-else-if="processResultViz" class="signal-viz">
        <div class="text-[10px] font-mono text-muted-foreground uppercase mb-2">process_result</div>
        <div class="transform-flow">
          <div class="flow-value" :style="{ borderColor: colorHex + '40', color: colorHex }">
            {{ processResultViz.input.toFixed(2) }}
          </div>
          <div class="flow-arrow">
            <svg width="40" height="20" viewBox="0 0 40 20" class="text-muted-foreground">
              <line x1="0" y1="10" x2="30" y2="10" stroke="currentColor" stroke-width="1" />
              <polygon points="30,6 38,10 30,14" fill="currentColor" />
            </svg>
            <span class="flow-formula">
              {{ processResultViz.coeff != null ? `×${processResultViz.coeff}` : '' }}{{ processResultViz.offset ? ` +${processResultViz.offset}` : '' }}
            </span>
          </div>
          <div class="flow-value flow-result" :style="{ borderColor: colorHex + '60', color: colorHex }">
            {{ processResultViz.result.toFixed(2) }}
          </div>
        </div>
      </div>

      <!-- 通用 key-value fallback -->
      <div v-else-if="genericEntries" class="signal-viz">
        <div class="text-[10px] font-mono text-muted-foreground uppercase mb-2">{{ signalType || 'signal' }}</div>
        <div class="kv-list">
          <div v-for="[key, val] in genericEntries" :key="key" class="kv-row">
            <span class="kv-key">{{ key }}</span>
            <span class="kv-val" :style="{ color: colorHex }">{{ val }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="robot.last_error" class="error-section">
      <div class="flex items-center gap-1.5 text-destructive text-xs mb-1">
        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Error</span>
      </div>
      <div class="text-xs text-muted-foreground bg-destructive/10 rounded-(--theme-radius) p-2 border-(length:--theme-border-width) border-destructive/30 truncate">
        {{ robot.last_error }}
      </div>
    </div>

    <!-- Footer -->
    <div class="flex items-center gap-1.5 pt-3 border-t border-border text-[10px] text-muted-foreground">
      <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>Updated {{ formattedTime }}</span>
    </div>
  </Card>
</template>

<style scoped>
.robot-card {
  user-select: none;
  touch-action: none;
}

.robot-card:hover {
  box-shadow: var(--theme-shadow-card-hover) !important;
}

.robot-card.dragging {
  box-shadow: var(--theme-shadow-card-hover) !important;
  z-index: 1000;
}

/* --- Signal Count --- */
.signal-count {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  display: inline-flex;
  align-items: center;
}

/* --- Signal Section --- */
.signal-section {
  margin-bottom: 12px;
}

.section-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--theme-muted-foreground);
  margin-bottom: 8px;
  font-weight: 600;
}

.signal-viz {
  background: var(--theme-muted);
  border-radius: var(--theme-radius);
  padding: 12px;
  border: var(--theme-border-width) solid var(--theme-border);
}

/* --- Progress Bar --- */
.progress-track {
  height: 6px;
  border-radius: 3px;
  background: var(--theme-border);
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}

/* --- Transform Flow --- */
.transform-flow {
  display: flex;
  align-items: center;
  gap: 4px;
}

.flow-value {
  font-family: "JetBrains Mono", monospace;
  font-size: 15px;
  font-weight: 600;
  padding: 6px 10px;
  border-radius: var(--theme-radius);
  border: var(--theme-border-width) solid;
  background: var(--theme-background);
  white-space: nowrap;
}

.flow-result {
  font-size: 17px;
}

.flow-arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.flow-formula {
  font-family: "JetBrains Mono", monospace;
  font-size: 9px;
  color: var(--theme-muted-foreground);
  margin-top: 2px;
  white-space: nowrap;
}

/* --- KV List --- */
.kv-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kv-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 2px 0;
}

.kv-key {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  color: var(--theme-muted-foreground);
}

.kv-val {
  font-family: "JetBrains Mono", monospace;
  font-size: 12px;
  font-weight: 500;
  max-width: 60%;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* --- Error Section --- */
.error-section {
  margin-bottom: 12px;
}
</style>
