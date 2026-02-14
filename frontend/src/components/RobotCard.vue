<script setup>
import { computed, ref } from "vue";

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

// Drag state
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });

// Computed
const statusColor = computed(() => {
  switch (props.robot.state) {
    case "running":
      return "text-neon-green";
    case "error":
      return "text-neon-pink";
    case "stopped":
      return "text-slate-400";
    case "disabled":
      return "text-slate-500";
    default:
      return "text-neon-yellow";
  }
});

const statusBg = computed(() => {
  switch (props.robot.state) {
    case "running":
      return "bg-neon-green";
    case "error":
      return "bg-neon-pink";
    case "stopped":
      return "bg-slate-400";
    case "disabled":
      return "bg-slate-500";
    default:
      return "bg-neon-yellow";
  }
});

const formattedTime = computed(() => {
  if (!props.robot.updated_at) return "-";
  const date = new Date(props.robot.updated_at);
  return date.toLocaleTimeString("zh-CN", { 
    hour: "2-digit", 
    minute: "2-digit", 
    second: "2-digit" 
  });
});

const latestSignal = computed(() => {
  return props.robot.latest_signal || null;
});

const signalData = computed(() => {
  if (!latestSignal.value?.data) return null;
  try {
    return JSON.stringify(latestSignal.value.data, null, 2);
  } catch {
    return String(latestSignal.value.data);
  }
});

// Methods
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
</script>

<template>
  <div
    class="card-robot w-[340px]"
    :class="{ 'dragging': isDragging }"
    :style="{
      left: `calc(50% + ${robot.position.x}px)`,
      top: `calc(50% + ${robot.position.y}px)`,
      transform: 'translate(-50%, -50%)',
    }"
    @mousedown="onMouseDown"
  >
    <!-- Header -->
    <div class="flex items-center gap-3 mb-4">
      <div class="relative">
        <div class="w-3 h-3 rounded-full" :class="statusBg" 
             :style="robot.state === 'running' ? 'box-shadow: 0 0 10px currentColor; animation: pulse 2s infinite;' : ''"></div>
        <div v-if="robot.state === 'running'" 
             class="absolute inset-0 w-3 h-3 rounded-full bg-neon-green animate-ping opacity-30"></div>
      </div>
      <h4 class="font-display font-semibold text-white text-sm truncate flex-1">
        {{ robot.robot_type }}
      </h4>
      <span class="text-xs font-mono px-2 py-0.5 rounded bg-surface text-slate-400 uppercase">
        {{ robot.state || "idle" }}
      </span>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-2 gap-3 mb-4">
      <div class="bg-surface/50 rounded-lg p-2.5">
        <div class="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Signals In</div>
        <div class="font-mono text-lg text-neon-cyan">{{ robot.signals_in || 0 }}</div>
      </div>
      <div class="bg-surface/50 rounded-lg p-2.5">
        <div class="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Signals Out</div>
        <div class="font-mono text-lg text-neon-purple">{{ robot.signals_out || 0 }}</div>
      </div>
    </div>

    <!-- Latest Signal -->
    <div v-if="latestSignal" class="mb-3">
      <div class="text-[10px] uppercase tracking-wider text-slate-500 mb-2">Latest Signal</div>
      <div class="bg-surface/30 rounded-lg p-3 border border-white/5">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-medium text-neon-cyan">{{ latestSignal.type || "signal" }}</span>
          <span class="text-xs text-slate-500">@ {{ formattedTime }}</span>
        </div>
        <pre v-if="signalData" class="text-[10px] font-mono text-slate-400 overflow-x-auto whitespace-pre-wrap break-all max-h-24 overflow-y-auto">{{ signalData }}</pre>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="robot.last_error" class="mb-3">
      <div class="flex items-center gap-2 text-neon-pink text-xs mb-1">
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
    <div class="flex items-center justify-between pt-3 border-t border-white/5">
      <div class="flex items-center gap-1.5 text-[10px] text-slate-500">
        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Updated {{ formattedTime }}</span>
      </div>
      <div class="flex items-center gap-1">
        <div class="w-1.5 h-1.5 rounded-full bg-surface"></div>
        <div class="w-1.5 h-1.5 rounded-full bg-surface"></div>
        <div class="w-1.5 h-1.5 rounded-full bg-surface"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card-robot {
  user-select: none;
  touch-action: none;
}

pre::-webkit-scrollbar {
  height: 4px;
  width: 4px;
}

pre::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
