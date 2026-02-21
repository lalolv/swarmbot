<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

export type Expression = "neutral" | "receiving" | "sending" | "happy" | "error";

const props = defineProps<{
  /** 机器人主题色 (hex) */
  color: string;
  /** 当前明暗模式 */
  colorScheme?: string;
  /** 机器人状态 */
  state?: string;
  /** 用于 SVG filter id 去重的唯一标识 */
  uid?: string;
  /** 尺寸缩放（基准 44×44） */
  size?: number;
  /** 表情类型 */
  expression?: Expression;
}>();

const expr = computed(() => props.expression || "neutral");
const neutralBlink = ref(false);

let blinkScheduleTimer: ReturnType<typeof setTimeout> | null = null;
let blinkCloseTimer: ReturnType<typeof setTimeout> | null = null;

function clearBlinkTimers(): void {
  if (blinkScheduleTimer) {
    clearTimeout(blinkScheduleTimer);
    blinkScheduleTimer = null;
  }
  if (blinkCloseTimer) {
    clearTimeout(blinkCloseTimer);
    blinkCloseTimer = null;
  }
}

function scheduleNextBlink(): void {
  const next = 2600 + Math.random() * 3200;
  blinkScheduleTimer = setTimeout(() => {
    neutralBlink.value = true;
    blinkCloseTimer = setTimeout(() => {
      neutralBlink.value = false;
      scheduleNextBlink();
    }, 130);
  }, next);
}

function startNeutralBlinkLoop(): void {
  clearBlinkTimers();
  neutralBlink.value = false;
  scheduleNextBlink();
}

function stopNeutralBlinkLoop(): void {
  clearBlinkTimers();
  neutralBlink.value = false;
}

watch(
  expr,
  (value) => {
    if (value === "neutral") {
      startNeutralBlinkLoop();
      return;
    }
    stopNeutralBlinkLoop();
  },
  { immediate: true }
);

onMounted(() => {
  if (expr.value === "neutral") {
    startNeutralBlinkLoop();
  }
});

onBeforeUnmount(() => {
  stopNeutralBlinkLoop();
});

interface Palette {
  bg: string;
  body: string;
  face: string;
  accentDot: string;
  eyeBlock: string;
  eyeLine: string;
}

const FALLBACK_COLOR = "#ea580c";

function parseHexColor(input: string): [number, number, number] | null {
  const color = input.trim().toLowerCase();
  if (!color.startsWith("#")) {
    return null;
  }

  const hex = color.slice(1);
  if (hex.length === 3) {
    const r = Number.parseInt(hex[0] + hex[0], 16);
    const g = Number.parseInt(hex[1] + hex[1], 16);
    const b = Number.parseInt(hex[2] + hex[2], 16);
    if (Number.isNaN(r) || Number.isNaN(g) || Number.isNaN(b)) {
      return null;
    }
    return [r, g, b];
  }

  if (hex.length === 6) {
    const r = Number.parseInt(hex.slice(0, 2), 16);
    const g = Number.parseInt(hex.slice(2, 4), 16);
    const b = Number.parseInt(hex.slice(4, 6), 16);
    if (Number.isNaN(r) || Number.isNaN(g) || Number.isNaN(b)) {
      return null;
    }
    return [r, g, b];
  }

  return null;
}

function toHex([r, g, b]: [number, number, number]): string {
  const hex = [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");
  return `#${hex}`;
}

function srgbToLinear(v: number): number {
  const n = v / 255;
  return n <= 0.04045 ? n / 12.92 : ((n + 0.055) / 1.055) ** 2.4;
}

function luminance([r, g, b]: [number, number, number]): number {
  const rl = srgbToLinear(r);
  const gl = srgbToLinear(g);
  const bl = srgbToLinear(b);
  return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl;
}

const palette = computed<Palette>(() => {
  const raw = props.color.trim().toLowerCase();
  const rgb = parseHexColor(raw) || parseHexColor(FALLBACK_COLOR);
  if (!rgb) {
    return {
      bg: FALLBACK_COLOR,
      face: FALLBACK_COLOR,
      body: "#f8f8f8",
      accentDot: "#f8f8f8",
      eyeBlock: "#f8f8f8",
      eyeLine: "#f8f8f8",
    };
  }

  const bg = toHex(rgb);
  const detail = props.colorScheme === "dark"
    ? "#0a0a0a"
    : luminance(rgb) > 0.48
      ? "#111111"
      : "#f8f8f8";

  return {
    bg,
    face: bg,
    body: detail,
    accentDot: detail,
    eyeBlock: detail,
    eyeLine: detail,
  };
});
const svgSize = computed(() => 44 * (props.size || 1));
</script>

<template>
  <div class="robot-avatar" :style="{ width: svgSize + 'px', height: svgSize + 'px' }">
    <svg :width="svgSize" :height="svgSize" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="1" y="1" width="42" height="42" rx="8.4" :fill="palette.bg" />

      <rect x="10" y="13" width="24" height="20" rx="6" :fill="palette.face" :stroke="palette.body" stroke-width="2.8" />

      <g class="robot-eyes" :class="`eyes-${expr}`">
        <template v-if="expr === 'receiving'">
          <circle cx="17.9" cy="23" r="2.5" :fill="palette.eyeBlock" />
          <circle cx="27.3" cy="23" r="1.35" :fill="palette.eyeLine" />
        </template>

        <template v-else-if="expr === 'sending'">
          <rect x="14.3" y="22.1" width="7.2" height="1.7" rx="0.85" :fill="palette.eyeBlock" />
          <rect x="23.7" y="22.25" width="7.2" height="1.5" rx="0.75" :fill="palette.eyeLine" />
        </template>

        <template v-else-if="expr === 'happy'">
          <path d="M14.5 23.6Q17.9 20.7 21.3 23.6" :stroke="palette.eyeBlock" stroke-width="1.5" stroke-linecap="round" fill="none" />
          <path d="M24 23.6Q27.3 20.9 30.6 23.6" :stroke="palette.eyeLine" stroke-width="1.5" stroke-linecap="round" fill="none" />
        </template>

        <template v-else-if="expr === 'error'">
          <g :stroke="palette.eyeBlock" stroke-width="1.3" stroke-linecap="round">
            <line x1="15" y1="21.1" x2="20.8" y2="24.9" />
            <line x1="20.8" y1="21.1" x2="15" y2="24.9" />
          </g>
          <g :stroke="palette.eyeLine" stroke-width="1.25" stroke-linecap="round">
            <line x1="24.2" y1="21.5" x2="30.8" y2="23.9" />
            <line x1="30.8" y1="21.5" x2="24.2" y2="23.9" />
          </g>
        </template>

        <template v-else>
          <template v-if="neutralBlink">
            <rect x="14.3" y="22.35" width="7.2" height="1.4" rx="0.7" :fill="palette.eyeBlock" />
            <rect x="23.7" y="22.35" width="7.2" height="1.4" rx="0.7" :fill="palette.eyeLine" />
          </template>
          <template v-else>
            <rect x="14.3" y="20.65" width="7.2" height="4.7" rx="1.2" :fill="palette.eyeBlock" />
            <rect x="23.7" y="20.65" width="7.2" height="4.7" rx="1.2" :fill="palette.eyeLine" />
          </template>
        </template>
      </g>

      <circle
        cx="22"
        cy="8"
        r="2"
        :fill="palette.accentDot"
        class="antenna-dot"
        :class="{
          'antenna-receiving': expr === 'receiving',
          'antenna-sending': expr === 'sending',
        }"
      />
    </svg>
  </div>
</template>

<style scoped>
.robot-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 0;
  flex-shrink: 0;
}

.antenna-dot {
  transform-box: fill-box;
  transform-origin: center;
}

.robot-eyes {
  transform-box: fill-box;
  transform-origin: center;
}

.antenna-receiving {
  animation: antenna-receive-jitter 0.45s ease-in-out infinite;
}

.antenna-sending {
  animation: antenna-send-jitter 0.45s ease-in-out infinite;
}

@keyframes antenna-receive-jitter {
  0%,
  100% {
    transform: translateY(0);
  }
  25% {
    transform: translateY(-0.6px);
  }
  75% {
    transform: translateY(0.6px);
  }
}

@keyframes antenna-send-jitter {
  0%,
  100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-0.7px);
  }
  75% {
    transform: translateX(0.7px);
  }
}

.eyes-receiving {
  animation: eyes-receive-pulse 0.6s ease-in-out infinite;
}

.eyes-sending {
  animation: eyes-send-focus 0.7s ease-in-out infinite;
}

.eyes-happy {
  animation: eyes-happy-bounce 0.5s ease-out;
}

.eyes-error {
  animation: eyes-error-shake 0.35s ease-in-out infinite;
}

@keyframes eyes-receive-pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.75;
    transform: scale(1.04);
  }
}

@keyframes eyes-send-focus {
  0%,
  100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(0.6px);
  }
}

@keyframes eyes-happy-bounce {
  0% {
    transform: translateY(0);
  }
  45% {
    transform: translateY(-0.8px);
  }
  100% {
    transform: translateY(0);
  }
}

@keyframes eyes-error-shake {
  0%,
  100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-0.5px);
  }
  75% {
    transform: translateX(0.5px);
  }
}
</style>
