import { defineStore } from "pinia";

import {
  cancelTask,
  createTask,
  createTaskEventSource,
  fetchRobotTypes,
  fetchTaskDetail,
  fetchTasks,
  purgeTask,
  type TaskItem,
  type TaskDetail,
  type CreateTaskPayload,
} from "@/api/client";

// ===== 类型定义 =====

export interface LatestSignal {
  type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface RobotState {
  robot_type: string;
  signals_in: number;
  signals_out: number;
  state: string;
  last_error: string | null;
  updated_at: string;
  latest_signal: LatestSignal | null;
}

export interface StreamCounts {
  data: number;
  output: number;
  control: number;
  unknown: number;
  [key: string]: number;
}

export interface CreateTaskForm {
  taskId: string;
  userId: string;
  name: string;
  description: string;
  selectedRobots: string[];
}

// ===== 工具函数 =====

function isoNow(): string {
  return new Date().toISOString();
}

function parseEventData(event: MessageEvent): Record<string, unknown> {
  try {
    return JSON.parse(event.data || "{}");
  } catch {
    return {};
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function isTaskNotFoundError(error: unknown): boolean {
  const message = String((error as Error)?.message || "");
  return message.includes("HTTP 404") || message.includes("Task not found");
}

function makeDefaultRobot(robotType: string): RobotState {
  return {
    robot_type: robotType,
    signals_in: 0,
    signals_out: 0,
    state: "idle",
    last_error: null,
    updated_at: isoNow(),
    latest_signal: null,
  };
}

// ===== Store =====

export const useObservabilityStore = defineStore("observability", {
  state: () => ({
    robotTypes: [] as string[],
    tasks: [] as TaskItem[],
    monitorTaskId: "",
    taskState: "idle",
    connectionState: "idle" as string,
    robots: {} as Record<string, RobotState>,
    streamCounts: {
      data: 0,
      output: 0,
      control: 0,
      unknown: 0,
    } as StreamCounts,
    eventCount: 0,
    lastError: "",
    _source: null as EventSource | null,
  }),

  getters: {
    robotList(state): RobotState[] {
      return Object.values(state.robots).sort((a, b) =>
        a.robot_type.localeCompare(b.robot_type)
      );
    },
  },

  actions: {
    async initialize() {
      const [tasksRes, robotsRes] = await Promise.all([
        fetchTasks(),
        fetchRobotTypes(),
      ]);
      this.tasks = tasksRes.items || [];
      this.robotTypes = robotsRes.robot_types || [];
      if (!this.monitorTaskId && this.tasks.length > 0) {
        this.monitorTaskId = this.tasks[0].task_id;
      }
    },

    async refreshTasks() {
      const res = await fetchTasks();
      this.tasks = res.items || [];
      if (!this.monitorTaskId && this.tasks.length > 0) {
        this.monitorTaskId = this.tasks[0].task_id;
      }
    },

    async createNewTask(form: CreateTaskForm) {
      const selectedRobots = form.selectedRobots.filter(Boolean);
      if (selectedRobots.length === 0) {
        throw new Error("至少选择一个机器人类型");
      }

      const payload: CreateTaskPayload = {
        task_id: form.taskId || undefined,
        user_id: form.userId || "",
        name: form.name || undefined,
        description: form.description || undefined,
        robots: selectedRobots,
        custom_config: {},
      };

      const result = await createTask(payload);
      await this.refreshTasks();
      this.monitorTaskId = result.task_id;
      await this.startMonitoring(result.task_id);
      return result;
    },

    async startMonitoring(taskId: string) {
      if (!taskId) {
        throw new Error("请先输入或选择任务 ID");
      }

      this.stopMonitoring();
      this.monitorTaskId = taskId;
      this.connectionState = "connecting";
      this.eventCount = 0;
      this.lastError = "";
      this.streamCounts = { data: 0, output: 0, control: 0, unknown: 0 };

      let detail: TaskDetail;
      try {
        detail = await this.fetchTaskDetailWithRetry(taskId);
      } catch (error) {
        if (isTaskNotFoundError(error)) {
          await this.refreshTasks();
          const stillExists = this.tasks.some(
            (item) => item.task_id === taskId
          );
          if (!stillExists) {
            this.monitorTaskId = this.tasks[0]?.task_id || "";
          }
          throw new Error(`任务不存在或已被清理: ${taskId}`);
        }
        throw error;
      }
      this.taskState = detail?.status?.state || "unknown";
      this.robots = {};
      this.upsertRobotsFromDetail(detail);

      const source = createTaskEventSource(taskId, true);
      source.onopen = () => {
        this.connectionState = "connected";
      };
      source.onerror = () => {
        this.connectionState = "reconnecting";
      };

      const forward =
        (eventType: string) => (event: MessageEvent) =>
          this.handleEvent(eventType, event);
      source.addEventListener("task_status", forward("task_status"));
      source.addEventListener("robot_status", forward("robot_status"));
      source.addEventListener("data_update", forward("data_update"));
      source.addEventListener("process_result", forward("process_result"));
      source.addEventListener("heartbeat", forward("heartbeat"));
      source.addEventListener("task_end", forward("task_end"));
      source.addEventListener("error", forward("error"));

      this._source = source;
    },

    async stopTask(taskId: string) {
      if (!taskId) {
        throw new Error("请先选择任务");
      }
      const result = await cancelTask(taskId);
      await this.refreshTasks();
      return result;
    },

    async cleanupTask(taskId: string) {
      if (!taskId) {
        throw new Error("请先选择任务");
      }
      const result = await purgeTask(taskId);
      if (this.monitorTaskId === taskId) {
        this.stopMonitoring();
        this.taskState = "idle";
        this.robots = {};
        this.eventCount = 0;
      }
      await this.refreshTasks();
      return result;
    },

    async fetchTaskDetailWithRetry(
      taskId: string,
      maxAttempts = 10,
      delayMs = 300
    ): Promise<TaskDetail> {
      let lastError: Error | null = null;
      for (let i = 0; i < maxAttempts; i += 1) {
        try {
          return await fetchTaskDetail(taskId);
        } catch (error) {
          lastError = error as Error;
          const message = String((error as Error)?.message || "");
          if (!message.includes("HTTP 404")) {
            throw error;
          }
          await sleep(delayMs);
        }
      }
      throw lastError || new Error(`Task not found after retry: ${taskId}`);
    },

    stopMonitoring() {
      if (this._source) {
        this._source.close();
        this._source = null;
      }
      if (this.connectionState !== "idle") {
        this.connectionState = "closed";
      }
    },

    handleEvent(eventType: string, event: MessageEvent) {
      this.eventCount += 1;
      const payload = parseEventData(event) as Record<string, any>;
      const stream = event.lastEventId?.split("|")[0] || "unknown";

      if (stream in this.streamCounts) {
        this.streamCounts[stream] += 1;
      } else {
        this.streamCounts.unknown += 1;
      }

      if (eventType === "task_status") {
        this.taskState = payload.state || this.taskState;
      }

      if (eventType === "robot_status") {
        const robotType = payload.robot_type || "unknown";
        const prev = this.robots[robotType] || makeDefaultRobot(robotType);
        this.robots = {
          ...this.robots,
          [robotType]: {
            ...prev,
            ...payload,
            updated_at: payload.timestamp || isoNow(),
          },
        };
      }

      if (eventType === "data_update" || eventType === "process_result") {
        const robotType = payload.robot_type || "unknown";
        const prev = this.robots[robotType] || makeDefaultRobot(robotType);
        this.robots = {
          ...this.robots,
          [robotType]: {
            ...prev,
            latest_signal: {
              type: payload.signal_type || eventType,
              data: payload.data || {},
              timestamp: payload.timestamp || isoNow(),
            },
            updated_at: payload.timestamp || isoNow(),
          },
        };
      }

      if (eventType === "error") {
        this.lastError = payload.message || "SSE stream error";
      }

      if (eventType === "task_end") {
        this.taskState = payload.state || this.taskState;
        this.connectionState = "ended";
      }
    },

    upsertRobotsFromDetail(detail: TaskDetail) {
      for (const robot of detail?.robots || []) {
        const robotType =
          typeof robot === "string" ? robot : (robot as { type: string }).type;
        if (!robotType) continue;
        const prev = this.robots[robotType] || makeDefaultRobot(robotType);
        this.robots = {
          ...this.robots,
          [robotType]: {
            ...prev,
            updated_at: detail?.status?.updated_at || prev.updated_at,
          },
        };
      }
    },

    async syncTaskRobots(taskId?: string) {
      const resolvedId = taskId || this.monitorTaskId;
      if (!resolvedId) {
        throw new Error("请先选择任务");
      }
      let detail: TaskDetail;
      try {
        detail = await fetchTaskDetail(resolvedId);
      } catch (error) {
        if (isTaskNotFoundError(error)) {
          await this.refreshTasks();
          const stillExists = this.tasks.some(
            (item) => item.task_id === resolvedId
          );
          if (!stillExists) {
            this.monitorTaskId = this.tasks[0]?.task_id || "";
          }
          throw new Error(`任务不存在或已被清理: ${resolvedId}`);
        }
        throw error;
      }
      this.taskState = detail?.status?.state || this.taskState;
      this.upsertRobotsFromDetail(detail);
      return detail;
    },
  },
});
