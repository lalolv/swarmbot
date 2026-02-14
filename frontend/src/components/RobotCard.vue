<script setup>
import { computed, ref } from "vue";
import RobotAvatar from "./RobotAvatar.vue";

const props = defineProps({
  robot: {
    type: Object,
    required: true,
  },
  scale: {
    type: Number,
    default: 1,
  },
});

const emit = defineEmits(["move"]);

// --- Neon 色板 ---
const NEON_PALETTE = [
  { name: "cyan",   color: "#00f0ff" },
  { name: "purple", color: "#b829ff" },
  { name: "pink",   color: "#ff2d95" },
  { name: "green",  color: "#00ff88" },
  { name: "orange", color: "#ff6b35" },
  { name: "yellow", color: "#ffee00" },
];

function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

const colorHex = computed(() => {
  const idx = hashString(props.robot.robot_type) % NEON_PALETTE.length;
  return NEON_PALETTE[idx].color;
});

// --- 拖拽 ---
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });

function onMouseDown(e) {
  e.stopPropagation();
  isDragging.value = true;
  dragStart.value = { x: e.clientX, y: e.clientY };
  document.addEventListener("mousemove", onMouseMove);
  document.addEventListener("mouseup", onMouseUp);
}

function onMouseMove(e) {
  if (!isDragging.value) return;
  const deltaX = e.clientX - dragStart.value.x;
  const deltaY = e.clientY - dragStart.value.y;
  emit("move", deltaX, deltaY);
  dragStart.value = { x: e.clientX, y: e.clientY };
}

function onMouseUp() {
  isDragging.value = false;
  document.removeEventListener("mousemove", onMouseMove);
  document.removeEventListener("mouseup", onMouseUp);
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

const signalData = computed(() => latestSignal.value?.data || null);

// data_update 可视化
const dataUpdateViz = computed(() => {
  if (signalType.value !== "data_update" || !signalData.value) return null;
  const { value, min_value, max_value } = signalData.value;
  if (value == null || min_value == null || max_value == null) return null;
  const range = max_value - min_value;
  const pct = range > 0 ? ((value - min_value) / range) * 100 : 0;
  return { value, min: min_value, max: max_value, pct: Math.max(0, Math.min(100, pct)) };
});

// process_result 可视化
const processResultViz = computed(() => {
  if (signalType.value !== "process_result" || !signalData.value) return null;
  const { input_value, coefficient, offset, result_value } = signalData.value;
  if (input_value == null || result_value == null) return null;
  return { input: input_value, coeff: coefficient, offset, result: result_value };
});

// 通用 key-value fallback
const genericEntries = computed(() => {
  if (!signalData.value || dataUpdateViz.value || processResultViz.value) return null;
  const entries = Object.entries(signalData.value).filter(
    ([k]) => k !== "timestamp" && k !== "source_type"
  );
  return entries.length > 0 ? entries : null;
});
</script>

<template>
  <div
    class="card-robot w-[340px]"
    :class="{ dragging: isDragging }"
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
        :state="robot.state"
        :uid="robot.robot_type"
      />

      <!-- Name + Counts -->
      <div class="flex-1 min-w-0">
        <h4 class="font-display font-semibold text-white text-sm truncate">
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
          <span class="text-[10px] font-mono text-slate-500 uppercase">data_update</span>
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
          <span class="text-[9px] font-mono text-slate-600">{{ dataUpdateViz.min }}</span>
          <span class="text-[9px] font-mono text-slate-600">{{ dataUpdateViz.max }}</span>
        </div>
      </div>

      <!-- process_result 转换流程可视化 -->
      <div v-else-if="processResultViz" class="signal-viz">
        <div class="text-[10px] font-mono text-slate-500 uppercase mb-2">process_result</div>
        <div class="transform-flow">
          <div class="flow-value" :style="{ borderColor: colorHex + '40', color: colorHex }">
            {{ processResultViz.input.toFixed(2) }}
          </div>
          <div class="flow-arrow">
            <svg width="40" height="20" viewBox="0 0 40 20" class="text-slate-600">
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
        <div class="text-[10px] font-mono text-slate-500 uppercase mb-2">{{ signalType || 'signal' }}</div>
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
      <div class="flex items-center gap-1.5 text-neon-pink text-xs mb-1">
        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Error</span>
      </div>
      <div class="text-xs text-slate-400 bg-neon-pink/10 rounded-lg p-2 border border-neon-pink/20 truncate">
        {{ robot.last_error }}
      </div>
    </div>

    <!-- Footer -->
    <div class="flex items-center gap-1.5 pt-3 border-t border-white/5 text-[10px] text-slate-500">
      <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>Updated {{ formattedTime }}</span>
    </div>
  </div>
</template>

<style scoped>
.card-robot {
  user-select: none;
  touch-action: none;
}

.card-robot:hover {
  box-shadow:
    0 8px 40px rgba(0, 0, 0, 0.5),
    0 0 0 1px var(--robot-color),
    0 0 30px color-mix(in srgb, var(--robot-color) 25%, transparent) !important;
}

.card-robot.dragging {
  box-shadow:
    0 12px 50px rgba(0, 0, 0, 0.6),
    0 0 0 2px var(--robot-color),
    0 0 50px color-mix(in srgb, var(--robot-color) 30%, transparent) !important;
}

/* --- Signal Count --- */
.signal-count {
  font-family: 'JetBrains Mono', monospace;
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
  color: rgb(100 116 139);
  margin-bottom: 8px;
}

.signal-viz {
  background: rgba(26, 26, 37, 0.4);
  border-radius: 10px;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

/* --- Progress Bar --- */
.progress-track {
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.06);
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
  font-family: 'JetBrains Mono', monospace;
  font-size: 15px;
  font-weight: 600;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid;
  background: rgba(0, 0, 0, 0.2);
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
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: rgb(100 116 139);
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
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: rgb(100 116 139);
}

.kv-val {
  font-family: 'JetBrains Mono', monospace;
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

/* --- Scrollbar --- */
.signal-viz::-webkit-scrollbar {
  height: 4px;
  width: 4px;
}

.signal-viz::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}
</style>
