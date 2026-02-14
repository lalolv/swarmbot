const CARD_WIDTH = 460;
const CARD_MIN_HEIGHT = 220;
const CARD_GAP = 40;
const CONTENT_PADDING_X = 14;
const CONTENT_START_Y = 42;
const LINE_HEIGHT = 20;
const MAX_TEXT_CHARS_PER_LINE = 56;

function roundedRect(ctx, x, y, width, height, radius) {
  const r = Math.min(radius, width / 2, height / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + width - r, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + r);
  ctx.lineTo(x + width, y + height - r);
  ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
  ctx.lineTo(x + r, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function stateColor(state) {
  if (state === "running") return "#0ea5e9";
  if (state === "error") return "#ef4444";
  if (state === "stopped") return "#64748b";
  if (state === "disabled") return "#94a3b8";
  return "#f59e0b";
}

function shortTime(value) {
  if (!value) return "-";
  return String(value).replace("T", " ").replace("Z", "").slice(5, 19);
}

function prettyJson(value) {
  try {
    return JSON.stringify(value ?? {}, null, 2);
  } catch {
    return "{}";
  }
}

function wrapTextByChars(text, maxChars = MAX_TEXT_CHARS_PER_LINE) {
  if (!text) {
    return [""];
  }
  if (text.length <= maxChars) {
    return [text];
  }

  const chunks = [];
  let index = 0;
  while (index < text.length) {
    chunks.push(text.slice(index, index + maxChars));
    index += maxChars;
  }
  return chunks;
}

function buildNodeLines(node) {
  const lines = [
    `state: ${node.state || "idle"}`,
    `signals in: ${node.signals_in || 0}`,
    `signals out: ${node.signals_out || 0}`,
  ];

  const latestSignal = node.latest_signal;
  if (latestSignal) {
    lines.push(`latest: ${latestSignal.type || "signal"} @ ${shortTime(latestSignal.timestamp)}`);
    lines.push("data:");
    const dataLines = prettyJson(latestSignal.data).split("\n");
    for (const raw of dataLines) {
      const wrapped = wrapTextByChars(raw);
      for (const item of wrapped) {
        lines.push(`  ${item}`);
      }
    }
  } else {
    lines.push("latest: -");
    lines.push("data: {}");
  }

  if (node.last_error) {
    const errorWrapped = wrapTextByChars(`err: ${String(node.last_error)}`);
    for (const line of errorWrapped) {
      lines.push(line);
    }
  }

  lines.push(`updated: ${shortTime(node.updated_at)}`);
  return lines;
}

export function computeRobotCardLayout(robots) {
  const total = robots.length;
  if (total === 0) {
    return [];
  }

  const withLines = robots.map((robot) => {
    const lines = buildNodeLines(robot);
    const dynamicHeight = CONTENT_START_Y + lines.length * LINE_HEIGHT + 22;
    return {
      ...robot,
      _lines: lines,
      h: Math.max(CARD_MIN_HEIGHT, dynamicHeight),
    };
  });

  const columns = Math.min(3, Math.max(1, Math.ceil(Math.sqrt(total))));
  const rowHeights = [];
  for (let row = 0; row < Math.ceil(total / columns); row += 1) {
    const rowItems = withLines.slice(row * columns, (row + 1) * columns);
    rowHeights[row] = rowItems.reduce((acc, item) => Math.max(acc, item.h), CARD_MIN_HEIGHT);
  }

  const rows = rowHeights.length;
  const totalWidth = columns * CARD_WIDTH + (columns - 1) * CARD_GAP;
  const totalHeight = rowHeights.reduce((acc, h) => acc + h, 0) + (rows - 1) * CARD_GAP;
  const startX = -totalWidth / 2;
  const startY = -totalHeight / 2;

  const rowOffsets = [];
  let cursorY = startY;
  for (let row = 0; row < rows; row += 1) {
    rowOffsets[row] = cursorY;
    cursorY += rowHeights[row] + CARD_GAP;
  }

  return withLines.map((robot, index) => {
    const row = Math.floor(index / columns);
    const col = index % columns;
    return {
      ...robot,
      x: startX + col * (CARD_WIDTH + CARD_GAP),
      y: rowOffsets[row],
      w: CARD_WIDTH,
      h: robot.h,
    };
  });
}

export function drawRobotNodeCard(ctx, node) {
  const tone = stateColor(node.state);

  ctx.save();
  ctx.shadowColor = "rgba(15, 23, 42, 0.14)";
  ctx.shadowBlur = 26;
  ctx.shadowOffsetY = 8;
  roundedRect(ctx, node.x, node.y, node.w, node.h, 18);
  ctx.fillStyle = "#ffffff";
  ctx.fill();
  ctx.restore();

  roundedRect(ctx, node.x, node.y, node.w, node.h, 18);
  ctx.lineWidth = 2;
  ctx.strokeStyle = "#e2e8f0";
  ctx.stroke();

  roundedRect(ctx, node.x + 12, node.y + 12, 9, 9, 4);
  ctx.fillStyle = tone;
  ctx.fill();

  ctx.fillStyle = "#0f172a";
  ctx.font = "700 16px Space Grotesk";
  ctx.textAlign = "left";
  ctx.fillText(node.robot_type || "unknown", node.x + 28, node.y + 22);

  const lines = Array.isArray(node._lines) ? node._lines : buildNodeLines(node);
  let cursorY = node.y + CONTENT_START_Y;
  for (const line of lines) {
    const isError = line.startsWith("err:");
    const isData = line.trimStart().startsWith("{") || line.trimStart().startsWith("}") || line.includes(":");
    if (isError) {
      ctx.fillStyle = "#b91c1c";
      ctx.font = "500 11px Manrope";
    } else if (isData) {
      ctx.fillStyle = "#475569";
      ctx.font = "500 11px Manrope";
    } else {
      ctx.fillStyle = "#334155";
      ctx.font = "600 11px Manrope";
    }
    ctx.fillText(line, node.x + CONTENT_PADDING_X, cursorY);
    cursorY += LINE_HEIGHT;
  }
}
