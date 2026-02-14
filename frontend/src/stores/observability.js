import { defineStore } from "pinia";

import {
  cancelTask,
  createTask,
  createTaskEventSource,
  fetchRobotTypes,
  fetchTaskDetail,
  fetchTasks,
  purgeTask,
} from "../api/client";

function isoNow() {
  return new Date().toISOString();
}

function parseEventData(event) {
  try {
    return JSON.parse(event.data || "{}");
  } catch {
    return {};
  }
}

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function isTaskNotFoundError(error) {
  const message = String(error?.message || "");
  return message.includes("HTTP 404") || message.includes("Task not found");
}

export const useObservabilityStore = defineStore("observability", {
  state: () => ({
    robotTypes: [],
    tasks: [],
    monitorTaskId: "",
    taskState: "idle",
    connectionState: "idle",
    robots: {},
    streamCounts: {
      data: 0,
      output: 0,
      control: 0,
      unknown: 0,
    },
    eventCount: 0,
    lastError: "",
    _source: null,
  }),

  getters: {
    robotList(state) {
      return Object.values(state.robots).sort((a, b) => a.robot_type.localeCompare(b.robot_type));
    },
  },

  actions: {
    async initialize() {
      const [tasksRes, robotsRes] = await Promise.all([fetchTasks(), fetchRobotTypes()]);
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

    async createNewTask(form) {
      const selectedRobots = form.selectedRobots.filter((name) => Boolean(name));
      if (selectedRobots.length === 0) {
        throw new Error("至少选择一个机器人类型");
      }

      const payload = {
        task_id: form.taskId || undefined,
        user_id: form.userId || "",
        robots: selectedRobots,
        custom_config: {
          poll_interval: Number(form.pollInterval || 2),
        },
      };

      const result = await createTask(payload);
      await this.refreshTasks();
      this.monitorTaskId = result.task_id;
      await this.startMonitoring(result.task_id);
      return result;
    },

    async startMonitoring(taskId) {
      if (!taskId) {
        throw new Error("请先输入或选择任务 ID");
      }

      this.stopMonitoring();
      this.monitorTaskId = taskId;
      this.connectionState = "connecting";
      this.eventCount = 0;
      this.lastError = "";
      this.streamCounts = { data: 0, output: 0, control: 0, unknown: 0 };

      let detail;
      try {
        detail = await this.fetchTaskDetailWithRetry(taskId);
      } catch (error) {
        if (isTaskNotFoundError(error)) {
          await this.refreshTasks();
          const stillExists = this.tasks.some((item) => item.task_id === taskId);
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

      const forward = (eventType) => (event) => this.handleEvent(eventType, event);
      source.addEventListener("task_status", forward("task_status"));
      source.addEventListener("robot_status", forward("robot_status"));
      source.addEventListener("data_update", forward("data_update"));
      source.addEventListener("process_result", forward("process_result"));
      source.addEventListener("heartbeat", forward("heartbeat"));
      source.addEventListener("task_end", forward("task_end"));
      source.addEventListener("error", forward("error"));

      this._source = source;
    },

    async stopTask(taskId) {
      if (!taskId) {
        throw new Error("请先选择任务");
      }
      const result = await cancelTask(taskId);
      await this.refreshTasks();
      return result;
    },

    async cleanupTask(taskId) {
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

    async fetchTaskDetailWithRetry(taskId, maxAttempts = 10, delayMs = 300) {
      let lastError = null;
      for (let i = 0; i < maxAttempts; i += 1) {
        try {
          return await fetchTaskDetail(taskId);
        } catch (error) {
          lastError = error;
          const message = String(error?.message || "");
          const isNotFound = message.includes("HTTP 404");
          if (!isNotFound) {
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

    handleEvent(eventType, event) {
      this.eventCount += 1;
      const payload = parseEventData(event);
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
        const prev = this.robots[robotType] || {
          robot_type: robotType,
          signals_in: 0,
          signals_out: 0,
          state: "idle",
          last_error: null,
          updated_at: isoNow(),
          latest_signal: null,
        };
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
        const prev = this.robots[robotType] || {
          robot_type: robotType,
          signals_in: 0,
          signals_out: 0,
          state: "idle",
          last_error: null,
          updated_at: isoNow(),
          latest_signal: null,
        };
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

    upsertRobotsFromDetail(detail) {
      for (const robot of detail?.robots || []) {
        const robotType = typeof robot === "string" ? robot : robot.type;
        if (!robotType) {
          continue;
        }
        const prev = this.robots[robotType] || {
          robot_type: robotType,
          signals_in: 0,
          signals_out: 0,
          state: "idle",
          last_error: null,
          updated_at: isoNow(),
          latest_signal: null,
        };
        this.robots = {
          ...this.robots,
          [robotType]: {
            ...prev,
            updated_at: detail?.status?.updated_at || prev.updated_at,
          },
        };
      }
    },

    async syncTaskRobots(taskId = this.monitorTaskId) {
      if (!taskId) {
        throw new Error("请先选择任务");
      }
      let detail;
      try {
        detail = await fetchTaskDetail(taskId);
      } catch (error) {
        if (isTaskNotFoundError(error)) {
          await this.refreshTasks();
          const stillExists = this.tasks.some((item) => item.task_id === taskId);
          if (!stillExists) {
            this.monitorTaskId = this.tasks[0]?.task_id || "";
          }
          throw new Error(`任务不存在或已被清理: ${taskId}`);
        }
        throw error;
      }
      this.taskState = detail?.status?.state || this.taskState;
      this.upsertRobotsFromDetail(detail);
      return detail;
    },
  },
});
