const API_BASE = import.meta.env.VITE_API_BASE || "";

// ===== 类型定义 =====

export interface TaskItem {
  task_id: string;
  status?: {
    state: string;
    updated_at?: string;
  };
  config?: {
    name?: string;
    description?: string;
  };
}

export interface TaskListResponse {
  items: TaskItem[];
}

export interface TaskDetail {
  task_id: string;
  robots: (string | { type: string })[];
  status?: {
    state: string;
    updated_at?: string;
  };
}

export interface RobotTypesResponse {
  robot_types: string[];
}

export interface CreateTaskPayload {
  task_id?: string;
  user_id: string;
  name?: string;
  description?: string;
  robots: string[];
  custom_config: Record<string, unknown>;
}

export interface CreateTaskResponse {
  accepted: boolean;
  task_id: string;
  message: string;
}

// ===== API 客户端 =====

async function requestJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string> || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`HTTP ${response.status} ${response.statusText}: ${detail}`);
  }

  return response.json();
}

export async function fetchTasks(): Promise<TaskListResponse> {
  return requestJson<TaskListResponse>("/api/v1/tasks");
}

export async function fetchTaskDetail(taskId: string): Promise<TaskDetail> {
  return requestJson<TaskDetail>(`/api/v1/tasks/${taskId}`);
}

export async function fetchRobotTypes(): Promise<RobotTypesResponse> {
  return requestJson<RobotTypesResponse>("/api/v1/tasks/robots");
}

export async function createTask(payload: CreateTaskPayload): Promise<CreateTaskResponse> {
  return requestJson<CreateTaskResponse>("/api/v1/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function cancelTask(taskId: string): Promise<unknown> {
  return requestJson(`/api/v1/tasks/${taskId}?purge=false`, {
    method: "DELETE",
  });
}

export async function purgeTask(taskId: string): Promise<unknown> {
  return requestJson(`/api/v1/tasks/${taskId}?purge=true`, {
    method: "DELETE",
  });
}

export function createTaskEventSource(taskId: string, history = true): EventSource {
  const params = new URLSearchParams({ history: history ? "1" : "0" });
  const path = `/api/v1/live/subscribe/${taskId}?${params.toString()}`;
  return new EventSource(`${API_BASE}${path}`);
}
