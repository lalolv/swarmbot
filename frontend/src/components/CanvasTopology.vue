<script setup>
import InfiniteCanvas from "ef-infinite-canvas";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

import { computeRobotCardLayout, drawRobotNodeCard } from "./canvas/robotNodeCard";

const props = defineProps({
  taskId: {
    type: String,
    required: true,
  },
  taskState: {
    type: String,
    required: true,
  },
  connectionState: {
    type: String,
    required: true,
  },
  robots: {
    type: Array,
    required: true,
  },
  eventCount: {
    type: Number,
    required: true,
  },
});

const hostRef = ref(null);
let infCanvas = null;
let ctx = null;

function drawGrid() {
  ctx.strokeStyle = "#e2e8f0";
  ctx.lineWidth = 1;
  for (let x = -1800; x <= 1800; x += 80) {
    ctx.beginPath();
    ctx.moveTo(x, -1200);
    ctx.lineTo(x, 1200);
    ctx.stroke();
  }
  for (let y = -1200; y <= 1200; y += 80) {
    ctx.beginPath();
    ctx.moveTo(-1800, y);
    ctx.lineTo(1800, y);
    ctx.stroke();
  }
}

function drawHeader() {
  ctx.fillStyle = "#0f172a";
  ctx.font = "700 20px Space Grotesk";
  ctx.textAlign = "left";
  ctx.fillText("Infinite Canvas Task Monitor", -1700, -1120);

  ctx.fillStyle = "#475569";
  ctx.font = "600 13px Manrope";
  ctx.fillText(`task: ${props.taskId || "-"}`, -1700, -1092);
  ctx.fillText(`state: ${props.taskState} / stream: ${props.connectionState}`, -1700, -1070);
  ctx.fillText(`robots: ${props.robots.length} / events: ${props.eventCount}`, -1700, -1048);
  ctx.fillText("tip: drag to pan, wheel to zoom", -1700, -1026);
}

function drawEmptyState() {
  ctx.fillStyle = "#334155";
  ctx.font = "600 20px Space Grotesk";
  ctx.textAlign = "center";
  ctx.fillText("No robots in this task yet", 0, 40);
  ctx.fillStyle = "#64748b";
  ctx.font = "600 13px Manrope";
  ctx.fillText("Create task with robots or wait for runtime sync", 0, 64);
}

function render() {
  if (!ctx) {
    return;
  }

  ctx.clearRect(-2200, -1600, 4400, 3200);
  drawGrid();
  drawHeader();

  const nodes = computeRobotCardLayout(props.robots);
  if (nodes.length === 0) {
    drawEmptyState();
    return;
  }

  for (const node of nodes) {
    drawRobotNodeCard(ctx, node);
  }
}

onMounted(() => {
  const canvasEl = hostRef.value;
  if (!canvasEl) {
    return;
  }
  infCanvas = new InfiniteCanvas(canvasEl);
  ctx = infCanvas.getContext("2d");
  render();
});

watch(
  () => [props.taskId, props.taskState, props.connectionState, props.robots, props.eventCount],
  () => {
    render();
  },
  { deep: true },
);

onBeforeUnmount(() => {
  infCanvas = null;
  ctx = null;
});
</script>

<template>
  <section class="rounded-3xl bg-white/85 p-4 shadow-panel backdrop-blur">
    <h3 class="mb-3 font-display text-lg text-ink">Infinite Canvas Monitor</h3>
    <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <canvas ref="hostRef" class="h-[680px] w-full" width="1600" height="1000" />
    </div>
  </section>
</template>
