import { defineStore } from "pinia";

import {
  createTask,
  createTaskEventSource,
  createTasksEventSource,
  deleteTask as apiDeleteTask,
  fetchRobotTypes,
  fetchTaskDetail,
  fetchTasks,
  sleepTask as apiSleepTask,
  wakeTask as apiWakeTask,
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

interface CommandReceiptEvent {
  type: "command_receipt";
  command_id: string;
  task_id: string;
  action: string;
  status: "accepted" | "applied" | "rejected";
  reason?: string;
}

interface TaskProjectionUpdatedEvent {
  type: "task_projection_updated";
  task_id: string;
  version: number;
  snapshot: TaskItem;
}

interface TaskProjectionDeletedEvent {
  type: "task_projection_deleted";
  task_id: string;
  version: number;
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
    robotsByTaskId: {} as Record<string, Record<string, RobotState>>,
    streamCounts: {
      data: 0,
      output: 0,
      control: 0,
      unknown: 0,
    } as StreamCounts,
    eventCount: 0,
    lastError: "",
    _source: null as EventSource | null,
    _monitorSessionId: 0,
    _tasksSource: null as EventSource | null,
    taskVersions: {} as Record<string, number>,
    pendingCommandsByTaskId: {} as Record<string, Record<string, string>>,
  }),

  getters: {
    robotList(state): RobotState[] {
      const taskRobots = state.robotsByTaskId[state.monitorTaskId] || {};
      return Object.values(taskRobots).sort((a, b) =>
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
      this.taskVersions = {};
      for (const task of this.tasks) {
        this.taskVersions[task.task_id] = 0;
      }
      this.robotTypes = robotsRes.robot_types || [];
      this.connectTasksFeed();
    },

    connectTasksFeed() {
      if (this._tasksSource) {
        return;
      }
      const source = createTasksEventSource(true);
      source.onopen = () => {
        // noop
      };
      source.onerror = () => {
        // 浏览器会自动重连
      };
      source.addEventListener("command_receipt", (event: MessageEvent) => {
        this.handleTaskFeedEvent("command_receipt", event);
      });
      source.addEventListener("task_projection_updated", (event: MessageEvent) => {
        this.handleTaskFeedEvent("task_projection_updated", event);
      });
      source.addEventListener("task_projection_deleted", (event: MessageEvent) => {
        this.handleTaskFeedEvent("task_projection_deleted", event);
      });
      this._tasksSource = source;
    },

    disconnectTasksFeed() {
      if (this._tasksSource) {
        this._tasksSource.close();
        this._tasksSource = null;
      }
    },

    async refreshTasks() {
      const res = await fetchTasks();
      this.tasks = res.items || [];
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
        robots: selectedRobots.map((type) => ({ type })),
        custom_config: {},
      };

      const result = await createTask(payload);
      this.stopMonitoring();
      this.monitorTaskId = result.task_id;
      this.taskState = "pending";
      this.robotsByTaskId = {
        ...this.robotsByTaskId,
        [result.task_id]: {},
      };
      this.eventCount = 0;
      this.pendingCommandsByTaskId = {
        ...this.pendingCommandsByTaskId,
        [result.task_id]: {
          ...(this.pendingCommandsByTaskId[result.task_id] || {}),
          [result.command_id]: "create",
        },
      };
      return result;
    },

    async startMonitoring(taskId: string) {
      if (!taskId) {
        throw new Error("请先输入或选择任务 ID");
      }

      this.stopMonitoring();
      const sessionId = this._monitorSessionId;
      this.monitorTaskId = taskId;
      this.connectionState = "connecting";
      this.eventCount = 0;
      this.lastError = "";
      this.streamCounts = { data: 0, output: 0, control: 0, unknown: 0 };
      this.robotsByTaskId = {
        ...this.robotsByTaskId,
        [taskId]: {},
      };

      let detail: TaskDetail;
      try {
        detail = await fetchTaskDetail(taskId);
      } catch (error) {
        if (isTaskNotFoundError(error)) {
          await this.refreshTasks();
          const stillExists = this.tasks.some(
            (item) => item.task_id === taskId
          );
          if (!stillExists) {
            this.monitorTaskId = "";
          }
          throw new Error(`任务不存在或已被清理: ${taskId}`);
        }
        throw error;
      }
      if (sessionId !== this._monitorSessionId || this.monitorTaskId !== taskId) {
        return;
      }
      this.taskState = detail?.status?.state || "unknown";
      this.upsertRobotsFromDetail(detail, taskId);

      // 静止状态无需 SSE 推送
      const STATIC_STATES = new Set(["sleeping", "completed", "failed", "cancelled"]);
      if (STATIC_STATES.has(this.taskState)) {
        this.connectionState = "ended";
        return;
      }

      const source = createTaskEventSource(taskId, true);
      source.onopen = () => {
        if (sessionId !== this._monitorSessionId || this.monitorTaskId !== taskId) {
          source.close();
          return;
        }
        this.connectionState = "connected";
      };
      source.onerror = () => {
        if (sessionId !== this._monitorSessionId || this.monitorTaskId !== taskId) {
          source.close();
          return;
        }
        this.connectionState = "reconnecting";
      };

      const forward =
        (eventType: string) => (event: MessageEvent) =>
          this.handleEvent(eventType, event, taskId, sessionId);
      source.addEventListener("task_status", forward("task_status"));
      source.addEventListener("robot_status", forward("robot_status"));
      source.addEventListener("data_update", forward("data_update"));
      source.addEventListener("process_result", forward("process_result"));
      source.addEventListener("heartbeat", forward("heartbeat"));
      source.addEventListener("task_end", forward("task_end"));
      source.addEventListener("error", forward("error"));

      this._source = source;
    },

    async sleepTask(taskId: string) {
      if (!taskId) {
        throw new Error("请先选择任务");
      }
      const result = await apiSleepTask(taskId);
      this.pendingCommandsByTaskId = {
        ...this.pendingCommandsByTaskId,
        [taskId]: {
          ...(this.pendingCommandsByTaskId[taskId] || {}),
          [result.command_id]: "sleep",
        },
      };
      return result;
    },

    async wakeTask(taskId: string) {
      if (!taskId) {
        throw new Error("请先选择任务");
      }
      const result = await apiWakeTask(taskId);
      this.pendingCommandsByTaskId = {
        ...this.pendingCommandsByTaskId,
        [taskId]: {
          ...(this.pendingCommandsByTaskId[taskId] || {}),
          [result.command_id]: "wake",
        },
      };
      return result;
    },

    async cleanupTask(taskId: string) {
      if (!taskId) {
        throw new Error("请先选择任务");
      }
      const result = await apiDeleteTask(taskId);
      this.pendingCommandsByTaskId = {
        ...this.pendingCommandsByTaskId,
        [taskId]: {
          ...(this.pendingCommandsByTaskId[taskId] || {}),
          [result.command_id]: "delete",
        },
      };
      if (this.monitorTaskId === taskId) {
        this.stopMonitoring();
        this.taskState = "idle";
        this.robotsByTaskId = {
          ...this.robotsByTaskId,
          [taskId]: {},
        };
        this.eventCount = 0;
      }
      return result;
    },

    stopMonitoring() {
      if (this._source) {
        this._source.close();
        this._source = null;
      }
      this._monitorSessionId += 1;
      if (this.connectionState !== "idle") {
        this.connectionState = "closed";
      }
    },

    handleTaskFeedEvent(eventType: string, event: MessageEvent) {
      const payload = parseEventData(event) as
        | CommandReceiptEvent
        | TaskProjectionUpdatedEvent
        | TaskProjectionDeletedEvent;

      if (eventType === "command_receipt") {
        const receipt = payload as CommandReceiptEvent;
        const current = this.pendingCommandsByTaskId[receipt.task_id] || {};
        if (receipt.status === "applied" || receipt.status === "rejected") {
          const next = { ...current };
          delete next[receipt.command_id];
          this.pendingCommandsByTaskId = {
            ...this.pendingCommandsByTaskId,
            [receipt.task_id]: next,
          };
        }
        if (receipt.status === "rejected" && receipt.reason) {
          this.lastError = receipt.reason;
        }
        return;
      }

      if (eventType === "task_projection_deleted") {
        const deleted = payload as TaskProjectionDeletedEvent;
        const nextVersion = Number(deleted.version || 0);
        const prevVersion = Number(this.taskVersions[deleted.task_id] || 0);
        if (nextVersion <= prevVersion) {
          return;
        }
        this.taskVersions = {
          ...this.taskVersions,
          [deleted.task_id]: nextVersion,
        };
        this.tasks = this.tasks.filter((item) => item.task_id !== deleted.task_id);
        const nextRobotsByTaskId = { ...this.robotsByTaskId };
        delete nextRobotsByTaskId[deleted.task_id];
        this.robotsByTaskId = nextRobotsByTaskId;
        const nextPendingByTaskId = { ...this.pendingCommandsByTaskId };
        delete nextPendingByTaskId[deleted.task_id];
        this.pendingCommandsByTaskId = nextPendingByTaskId;
        if (this.monitorTaskId === deleted.task_id) {
          this.monitorTaskId = "";
          this.taskState = "idle";
          this.stopMonitoring();
        }
        return;
      }

      if (eventType === "task_projection_updated") {
        const updated = payload as TaskProjectionUpdatedEvent;
        const nextVersion = Number(updated.version || 0);
        const prevVersion = Number(this.taskVersions[updated.task_id] || 0);
        if (nextVersion <= prevVersion) {
          return;
        }
        this.taskVersions = {
          ...this.taskVersions,
          [updated.task_id]: nextVersion,
        };

        const idx = this.tasks.findIndex((item) => item.task_id === updated.task_id);
        if (idx >= 0) {
          const next = this.tasks.slice();
          next[idx] = updated.snapshot;
          this.tasks = next;
        } else {
          this.tasks = [...this.tasks, updated.snapshot];
        }

        if (this.monitorTaskId === updated.task_id) {
          const nextState = updated.snapshot?.status?.state || this.taskState;
          this.taskState = nextState;
          if ((nextState === "pending" || nextState === "running") && !this._source) {
            this.startMonitoring(updated.task_id).catch(() => {
              // 仅在事件驱动下尽力重连
            });
          }
        }
      }
    },

    handleEvent(eventType: string, event: MessageEvent, taskId: string, sessionId: number) {
      if (sessionId !== this._monitorSessionId) {
        return;
      }
      if (this.monitorTaskId !== taskId) {
        return;
      }

      this.eventCount += 1;
      const payload = parseEventData(event) as Record<string, any>;
      const stream = event.lastEventId?.split("|")[0] || "unknown";

      if (stream in this.streamCounts) {
        this.streamCounts[stream] += 1;
      } else {
        this.streamCounts.unknown += 1;
      }

      if (eventType === "task_status") {
        if (payload.task_id && payload.task_id !== taskId) {
          return;
        }
        this.taskState = payload.state || this.taskState;
        const idx = this.tasks.findIndex((item) => item.task_id === taskId);
        if (idx >= 0) {
          const task = this.tasks[idx];
          const next = this.tasks.slice();
          next[idx] = {
            ...task,
            status: {
              ...(task.status || { state: this.taskState }),
              state: payload.state || this.taskState,
              updated_at: payload.updated_at || isoNow(),
            },
          };
          this.tasks = next;
        }
      }

      if (eventType === "robot_status") {
        const robotType = payload.robot_type || "unknown";
        if (payload.task_id && payload.task_id !== taskId) {
          return;
        }
        const taskRobots = this.robotsByTaskId[taskId] || {};
        const prev = taskRobots[robotType] || makeDefaultRobot(robotType);
        this.robotsByTaskId = {
          ...this.robotsByTaskId,
          [taskId]: {
            ...taskRobots,
            [robotType]: {
              ...prev,
              ...payload,
              updated_at: payload.timestamp || isoNow(),
            },
          },
        };
      }

      if (eventType === "data_update" || eventType === "process_result") {
        const robotType = payload.robot_type || "unknown";
        if (payload.task_id && payload.task_id !== taskId) {
          return;
        }
        const taskRobots = this.robotsByTaskId[taskId] || {};
        const prev = taskRobots[robotType] || makeDefaultRobot(robotType);
        this.robotsByTaskId = {
          ...this.robotsByTaskId,
          [taskId]: {
            ...taskRobots,
            [robotType]: {
              ...prev,
              latest_signal: {
                type: payload.signal_type || eventType,
                data: payload.data || {},
                timestamp: payload.timestamp || isoNow(),
              },
              updated_at: payload.timestamp || isoNow(),
            },
          },
        };
      }

      if (eventType === "error") {
        // payload.message 为空说明是连接关闭触发的 error 事件，非业务错误，忽略
        const message = payload.message as string | undefined;
        if (message) {
          this.lastError = message;
        }
      }

      if (eventType === "task_end") {
        this.taskState = payload.state || this.taskState;
        this.connectionState = "ended";
        // 主动关闭 EventSource，防止浏览器自动重连触发 connection error
        this.stopMonitoring();
      }
    },

    upsertRobotsFromDetail(detail: TaskDetail, taskId?: string) {
      const resolvedTaskId = taskId || this.monitorTaskId;
      if (!resolvedTaskId) {
        return;
      }
      const nextTaskRobots: Record<string, RobotState> = {};
      for (const robot of detail?.robots || []) {
        const robotType = robot.type;
        if (!robotType) continue;
        const prev = makeDefaultRobot(robotType);
        nextTaskRobots[robotType] = {
          ...prev,
          updated_at: detail?.status?.updated_at || prev.updated_at,
        };
      }
      this.robotsByTaskId = {
        ...this.robotsByTaskId,
        [resolvedTaskId]: nextTaskRobots,
      };
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
            this.monitorTaskId = "";
          }
          throw new Error(`任务不存在或已被清理: ${resolvedId}`);
        }
        throw error;
      }
      this.taskState = detail?.status?.state || this.taskState;
      this.upsertRobotsFromDetail(detail, resolvedId);
      return detail;
    },

    hasPendingAction(taskId: string, action?: string): boolean {
      if (!taskId) return false;
      const pending = this.pendingCommandsByTaskId[taskId] || {};
      const values = Object.values(pending);
      if (!action) return values.length > 0;
      return values.includes(action);
    },
  },
});
