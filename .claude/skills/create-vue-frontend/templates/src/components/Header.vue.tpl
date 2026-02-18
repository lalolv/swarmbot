<script setup lang="ts">
import { computed, reactive, ref } from "vue";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogHeader, DialogFooter } from "@/components/ui/dialog";
import ThemeSwitcher from "@/components/ThemeSwitcher.vue";
import type { TaskItem } from "@/api/client";

const props = defineProps<{
  tasks: TaskItem[];
  robotTypes: string[];
  currentTaskId: string;
  isSubscribed: boolean;
  connectionState: string;
}>();

const emit = defineEmits<{
  "create-task": [form: any];
  "select-task": [taskId: string];
  subscribe: [taskId: string];
  unsubscribe: [];
  "delete-task": [taskId: string];
  "refresh-tasks": [];
}>();

// Create task modal
const showCreateModal = ref(false);
const creating = ref(false);
const createForm = reactive({
  taskId: "",
  userId: "",
  selectedRobots: [] as string[],
});

// Task list dropdown
const showTaskList = ref(false);

// Computed
const canSubscribe = computed(() => props.currentTaskId && !props.isSubscribed);
const canUnsubscribe = computed(() => props.isSubscribed);
const canDelete = computed(() => props.currentTaskId);

const connectionBadgeVariant = computed(() => {
  switch (props.connectionState) {
    case "connected":
      return "success" as const;
    case "connecting":
    case "reconnecting":
      return "secondary" as const;
    case "error":
    case "closed":
      return "destructive" as const;
    default:
      return "outline" as const;
  }
});

// Methods
function toggleRobot(robotType: string) {
  const index = createForm.selectedRobots.indexOf(robotType);
  if (index > -1) {
    createForm.selectedRobots.splice(index, 1);
  } else {
    createForm.selectedRobots.push(robotType);
  }
}

async function submitCreate() {
  if (createForm.selectedRobots.length === 0) {
    alert("请至少选择一个机器人类型");
    return;
  }

  creating.value = true;
  try {
    emit("create-task", { ...createForm });
    showCreateModal.value = false;
    createForm.taskId = "";
    createForm.userId = "";
    createForm.selectedRobots = [];
  } finally {
    creating.value = false;
  }
}

function selectTask(taskId: string) {
  emit("select-task", taskId);
  showTaskList.value = false;
}

function toggleSubscription() {
  if (props.isSubscribed) {
    emit("unsubscribe");
  } else {
    emit("subscribe", props.currentTaskId);
  }
}

async function deleteTask() {
  if (!confirm(`确定要删除任务 "${props.currentTaskId}" 吗？`)) {
    return;
  }
  emit("delete-task", props.currentTaskId);
}
</script>

<template>
  <header
    class="fixed top-0 left-0 right-0 z-50 h-16 bg-card border-b-(length:--theme-border-width) border-border"
  >
    <div class="h-full px-4 flex items-center justify-between">
      <!-- Logo & Title -->
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-3">
          <div
            class="w-8 h-8 rounded-(--theme-radius) bg-primary flex items-center justify-center border-(length:--theme-border-width) border-border shadow-card"
          >
            <svg class="w-5 h-5 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <div>
            <h1 class="font-display text-lg font-bold text-foreground">{app_name}</h1>
            <p class="text-[10px] text-muted-foreground tracking-wider uppercase">{app_subtitle}</p>
          </div>
        </div>

        <!-- Connection Status -->
        <Badge :variant="connectionBadgeVariant" class="hidden sm:inline-flex">
          <span class="status-dot mr-1.5" :class="`status-${connectionState === 'connected' ? 'running' : connectionState === 'connecting' ? 'connecting' : 'idle'}`"></span>
          {{ connectionState }}
        </Badge>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-2">
        <!-- Theme Switcher -->
        <ThemeSwitcher />

        <!-- Create Task Button -->
        <Button @click="showCreateModal = true" size="sm">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span class="hidden sm:inline">创建任务</span>
        </Button>

        <!-- Task List Dropdown -->
        <div class="relative">
          <Button variant="outline" size="sm" @click="showTaskList = !showTaskList">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <span class="hidden sm:inline max-w-[120px] truncate">
              {{ currentTaskId || '选择任务' }}
            </span>
            <svg class="w-4 h-4 transition-transform" :class="{ 'rotate-180': showTaskList }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </Button>

          <!-- Task List Dropdown Menu -->
          <div
            v-if="showTaskList"
            class="absolute top-full right-0 mt-2 w-72 bg-card border-(length:--theme-border-width) border-border rounded-(--theme-radius) shadow-card-hover overflow-hidden animate-slide-down"
          >
            <div class="p-3 border-b border-border flex items-center justify-between">
              <span class="text-xs font-display font-semibold text-muted-foreground uppercase tracking-wider">任务列表</span>
              <button @click="$emit('refresh-tasks')" class="text-xs font-semibold text-primary hover:underline">
                刷新
              </button>
            </div>
            <div class="max-h-64 overflow-y-auto">
              <div v-if="tasks.length === 0" class="p-4 text-center text-sm text-muted-foreground">
                暂无任务
              </div>
              <button
                v-for="task in tasks"
                :key="task.task_id"
                @click="selectTask(task.task_id)"
                class="w-full px-4 py-3 text-left hover:bg-muted transition-colors flex items-center gap-3"
                :class="{ 'bg-primary/10': task.task_id === currentTaskId }"
              >
                <span class="status-dot" :class="task.status?.state === 'running' ? 'status-running' : 'status-idle'"></span>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-semibold text-foreground truncate">{{ task.task_id }}</div>
                  <div class="text-xs text-muted-foreground">{{ task.status?.state || 'unknown' }}</div>
                </div>
                <svg v-if="task.task_id === currentTaskId" class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Subscribe Toggle -->
        <Button
          v-if="canSubscribe"
          variant="secondary"
          size="sm"
          @click="toggleSubscription"
          :disabled="!currentTaskId"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <span class="hidden sm:inline">订阅</span>
        </Button>

        <Button
          v-else-if="canUnsubscribe"
          variant="outline"
          size="sm"
          @click="toggleSubscription"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <span class="hidden sm:inline">取消订阅</span>
        </Button>

        <!-- Delete Task -->
        <Button
          v-if="canDelete"
          variant="destructive"
          size="sm"
          @click="deleteTask"
          title="删除任务"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          <span class="hidden sm:inline">删除</span>
        </Button>
      </div>
    </div>

    <!-- Create Task Modal -->
    <Dialog :open="showCreateModal" @close="showCreateModal = false">
      <DialogHeader>
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-(--theme-radius) bg-primary/20 border-(length:--theme-border-width) border-border flex items-center justify-center">
            <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <div>
            <h3 class="font-display text-lg font-bold text-foreground">创建新任务</h3>
            <p class="text-xs text-muted-foreground">配置任务参数并选择机器人</p>
          </div>
        </div>
        <button @click="showCreateModal = false" class="text-muted-foreground hover:text-foreground transition-colors">
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </DialogHeader>

      <!-- Modal Body -->
      <div class="p-6 space-y-5">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-display font-semibold text-muted-foreground mb-2 uppercase tracking-wider">任务 ID</label>
            <Input v-model="createForm.taskId" placeholder="自动生成" />
          </div>
          <div>
            <label class="block text-xs font-display font-semibold text-muted-foreground mb-2 uppercase tracking-wider">用户 ID</label>
            <Input v-model="createForm.userId" placeholder="可选" />
          </div>
        </div>

        <div>
          <label class="block text-xs font-display font-semibold text-muted-foreground mb-3 uppercase tracking-wider">
            选择机器人 <span class="text-destructive">*</span>
          </label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="robotType in robotTypes"
              :key="robotType"
              @click="toggleRobot(robotType)"
              class="px-3 py-1.5 text-xs font-display font-semibold transition-all border-(length:--theme-border-width) border-border rounded-(--theme-radius)"
              :class="createForm.selectedRobots.includes(robotType)
                ? 'bg-primary text-primary-foreground shadow-card'
                : 'bg-background text-muted-foreground hover:bg-muted'"
            >
              {{ robotType }}
            </button>
          </div>
          <p v-if="createForm.selectedRobots.length === 0" class="mt-2 text-xs text-destructive font-semibold">
            请至少选择一个机器人
          </p>
        </div>
      </div>

      <DialogFooter>
        <Button variant="ghost" @click="showCreateModal = false">
          取消
        </Button>
        <Button
          @click="submitCreate"
          :disabled="creating || createForm.selectedRobots.length === 0"
          class="disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg v-if="creating" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
          <span>{{ creating ? '创建中...' : '创建任务' }}</span>
        </Button>
      </DialogFooter>
    </Dialog>
  </header>
</template>

<style scoped>
header {
  isolation: isolate;
}
</style>
