const API_BASE = import.meta.env.VITE_API_BASE || "";

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`HTTP ${response.status} ${response.statusText}: ${detail}`);
  }

  return response.json();
}

export async function fetchTasks() {
  return requestJson("/api/v1/tasks");
}

export async function fetchTaskDetail(taskId) {
  return requestJson(`/api/v1/tasks/${taskId}`);
}

export async function fetchRobotTypes() {
  return requestJson("/api/v1/tasks/robots");
}

export async function createTask(payload) {
  return requestJson("/api/v1/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function cancelTask(taskId) {
  return requestJson(`/api/v1/tasks/${taskId}?purge=false`, {
    method: "DELETE",
  });
}

export async function purgeTask(taskId) {
  return requestJson(`/api/v1/tasks/${taskId}?purge=true`, {
    method: "DELETE",
  });
}

export function createTaskEventSource(taskId, history = true) {
  const params = new URLSearchParams({ history: history ? "1" : "0" });
  const path = `/api/v1/live/subscribe/${taskId}?${params.toString()}`;
  return new EventSource(`${API_BASE}${path}`);
}
