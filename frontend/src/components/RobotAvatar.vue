<script setup lang="ts">
import { computed } from "vue";

export type Expression = "neutral" | "receiving" | "sending" | "happy" | "error";

const props = defineProps<{
  /** 机器人主题色 (hex) */
  color: string;
  /** 机器人状态 */
  state?: string;
  /** 用于 SVG filter id 去重的唯一标识 */
  uid?: string;
  /** 尺寸缩放（基准 40×44） */
  size?: number;
  /** 表情类型 */
  expression?: Expression;
}>();

const expr = computed(() => props.expression || "neutral");

interface StateInfo {
  dotColor: string;
  glowRadius: number;
  bodyOpacity: number;
  glow: boolean;
}

const STATE_MAP: Record<string, StateInfo> = {
  running: { dotColor: "#00ff88", glowRadius: 3, bodyOpacity: 1, glow: true },
  error: { dotColor: "#ff2d95", glowRadius: 2, bodyOpacity: 0.85, glow: false },
  stopped: { dotColor: "#64748b", glowRadius: 0, bodyOpacity: 0.4, glow: false },
  disabled: { dotColor: "#475569", glowRadius: 0, bodyOpacity: 0.25, glow: false },
};
const STATE_DEFAULT: StateInfo = { dotColor: "#ffee00", glowRadius: 1.5, bodyOpacity: 0.65, glow: false };

const info = computed(() => STATE_MAP[props.state || ""] || STATE_DEFAULT);
const isRunning = computed(() => props.state === "running");
const filterId = computed(() => `glow-${props.uid || "robot"}`);
const svgWidth = computed(() => 40 * (props.size || 1));
const svgHeight = computed(() => 44 * (props.size || 1));
</script>

<template>
  <div
    class="robot-avatar"
    :class="{ 'avatar-glow': info.glow }"
    :style="{
      '--avatar-color': color,
      width: svgWidth + 'px',
      height: svgHeight + 'px',
    }"
  >
    <svg :width="svgWidth" :height="svgHeight" viewBox="0 0 40 44" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <filter :id="filterId" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur :stdDeviation="info.glowRadius" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <!-- 身体 -->
      <g :opacity="info.bodyOpacity">
        <rect x="6" y="12" width="28" height="22" rx="5"
              :stroke="color" stroke-width="1.5" fill="none" opacity="0.8" />
        <!-- 眼睛 -->
        <g class="robot-eyes" :class="`eyes-${expr}`">
          <!-- neutral: 正常方块眼 -->
          <template v-if="expr === 'neutral'">
            <rect x="12" y="19" width="5" height="5" rx="1.5" :fill="color" opacity="0.85" />
            <rect x="23" y="19" width="5" height="5" rx="1.5" :fill="color" opacity="0.85" />
          </template>
          <!-- receiving: 放大圆眼 + 闪烁 -->
          <template v-else-if="expr === 'receiving'">
            <circle cx="14.5" cy="21.5" r="3" :fill="color" opacity="0.9" />
            <circle cx="25.5" cy="21.5" r="3" :fill="color" opacity="0.9" />
          </template>
          <!-- sending: 窄眼（专注） -->
          <template v-else-if="expr === 'sending'">
            <rect x="11.5" y="20.5" width="6" height="2.5" rx="1.25" :fill="color" opacity="0.85" />
            <rect x="22.5" y="20.5" width="6" height="2.5" rx="1.25" :fill="color" opacity="0.85" />
          </template>
          <!-- happy: 弯弯眼 ^_^ -->
          <template v-else-if="expr === 'happy'">
            <path d="M11.5 22 Q14.5 18, 17.5 22" :stroke="color" stroke-width="1.8" stroke-linecap="round" fill="none" opacity="0.9" />
            <path d="M22.5 22 Q25.5 18, 28.5 22" :stroke="color" stroke-width="1.8" stroke-linecap="round" fill="none" opacity="0.9" />
          </template>
          <!-- error: X 形眼 -->
          <template v-else-if="expr === 'error'">
            <g opacity="0.9">
              <line x1="12" y1="18.5" x2="17" y2="23.5" :stroke="color" stroke-width="1.5" stroke-linecap="round" />
              <line x1="17" y1="18.5" x2="12" y2="23.5" :stroke="color" stroke-width="1.5" stroke-linecap="round" />
              <line x1="23" y1="18.5" x2="28" y2="23.5" :stroke="color" stroke-width="1.5" stroke-linecap="round" />
              <line x1="28" y1="18.5" x2="23" y2="23.5" :stroke="color" stroke-width="1.5" stroke-linecap="round" />
            </g>
          </template>
        </g>

        <!-- 嘴巴 -->
        <g class="robot-mouth" :class="`mouth-${expr}`">
          <!-- neutral: 短横线 -->
          <rect v-if="expr === 'neutral'" x="16" y="28" width="8" height="2" rx="1" :fill="color" opacity="0.5" />
          <!-- receiving: 张开的 O 形 -->
          <ellipse v-else-if="expr === 'receiving'" cx="20" cy="29" rx="2.5" ry="2" :stroke="color" stroke-width="1.2" fill="none" opacity="0.7" />
          <!-- sending: 向右箭头形 -->
          <path v-else-if="expr === 'sending'" d="M17 27.5 L22 29 L17 30.5" :stroke="color" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" fill="none" opacity="0.7" />
          <!-- happy: 微笑弧线 -->
          <path v-else-if="expr === 'happy'" d="M16 28 Q20 32, 24 28" :stroke="color" stroke-width="1.4" stroke-linecap="round" fill="none" opacity="0.7" />
          <!-- error: 波浪线 -->
          <path v-else-if="expr === 'error'" d="M15 29 Q17 27.5, 19 29 Q20 30, 21 29 Q23 27.5, 25 29" :stroke="color" stroke-width="1.2" stroke-linecap="round" fill="none" opacity="0.6" />
        </g>
        <rect x="2" y="18" width="4" height="8" rx="2" :fill="color" opacity="0.4" />
        <rect x="34" y="18" width="4" height="8" rx="2" :fill="color" opacity="0.4" />
        <line x1="15" y1="34" x2="15" y2="40" :stroke="color" stroke-width="1" opacity="0.3" />
        <line x1="25" y1="34" x2="25" y2="40" :stroke="color" stroke-width="1" opacity="0.3" />
        <line x1="12" y1="40" x2="28" y2="40" :stroke="color" stroke-width="1" opacity="0.3" stroke-linecap="round" />
      </g>

      <!-- 天线杆 -->
      <line x1="20" y1="12" x2="20" y2="6"
            :stroke="color" stroke-width="1.5" stroke-linecap="round" :opacity="info.bodyOpacity" />

      <!-- 天线状态灯 -->
      <circle v-if="isRunning" class="antenna-ping"
              cx="20" cy="5" r="3" :fill="info.dotColor" opacity="0.3" />
      <circle cx="20" cy="5" r="2.5"
              :fill="info.dotColor"
              :filter="`url(#${filterId})`"
              :class="{ 'antenna-pulse': isRunning }" />
    </svg>
  </div>
</template>

<style scoped>
.robot-avatar {
  position: relative;
  border-radius: var(--theme-radius);
  background: color-mix(in srgb, var(--avatar-color) 6%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.robot-avatar::after {
  content: "";
  position: absolute;
  inset: -2px;
  border-radius: var(--theme-radius);
  background: radial-gradient(
    circle,
    color-mix(in srgb, var(--avatar-color) 15%, transparent) 0%,
    transparent 70%
  );
  pointer-events: none;
  transition: opacity 0.3s;
}

.robot-avatar.avatar-glow::after {
  animation: avatar-breathe 2.5s ease-in-out infinite;
}

@keyframes avatar-breathe {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.antenna-pulse {
  animation: antenna-pulse 2s ease-in-out infinite;
  transform-origin: center;
}

@keyframes antenna-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.antenna-ping {
  animation: antenna-ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
  transform-origin: center;
}

@keyframes antenna-ping {
  0% { r: 3; opacity: 0.4; }
  100% { r: 7; opacity: 0; }
}

/* --- 表情动画 --- */
.robot-eyes,
.robot-mouth {
  transition: opacity 0.2s ease;
}

/* receiving: 眼睛闪烁 */
.eyes-receiving {
  animation: eyes-blink 0.6s ease-in-out infinite;
}

@keyframes eyes-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* receiving: 嘴巴缩放脉冲 */
.mouth-receiving {
  animation: mouth-pulse 0.6s ease-in-out infinite;
  transform-origin: 20px 29px;
}

@keyframes mouth-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

/* sending: 嘴巴向右平移动画 */
.mouth-sending {
  animation: mouth-send 0.8s ease-in-out infinite;
}

@keyframes mouth-send {
  0%, 100% { transform: translateX(0); opacity: 0.7; }
  50% { transform: translateX(2px); opacity: 1; }
}

/* happy: 轻微上下弹跳 */
.eyes-happy {
  animation: happy-bounce 0.5s ease-out;
}

@keyframes happy-bounce {
  0% { transform: translateY(0); }
  40% { transform: translateY(-2px); }
  100% { transform: translateY(0); }
}

/* error: 抖动 */
.eyes-error {
  animation: error-shake 0.4s ease-in-out infinite;
}

@keyframes error-shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-1px); }
  75% { transform: translateX(1px); }
}

.mouth-error {
  animation: error-wobble 1.2s ease-in-out infinite;
}

@keyframes error-wobble {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(1px); }
}
</style>
