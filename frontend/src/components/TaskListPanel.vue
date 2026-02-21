<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogHeader, DialogFooter } from "@/components/ui/dialog";
import type { TaskItem } from "@/api/client";

const props = defineProps<{
  tasks: TaskItem[];
  robotTypes: string[];
  currentTaskId: string;
}>();

const emit = defineEmits<{
  "create-task": [form: any];
  "select-task": [taskId: string];
  "delete-task": [taskId: string];
  "refresh-tasks": [];
}>();

// 面板折叠状态
const collapsed = ref(false);

// 创建任务弹窗
const showCreateModal = ref(false);
const creating = ref(false);
const createForm = reactive({
  taskId: "",
  userId: "",
  name: "",
  description: "",
  selectedRobots: [] as string[],
});

// Computed
const canDelete = computed(() => !!props.currentTaskId);

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
    createForm.name = "";
    createForm.description = "";
    createForm.selectedRobots = [];
  } finally {
    creating.value = false;
  }
}

function selectTask(taskId: string) {
  emit("select-task", taskId);
}

async function deleteTask() {
  if (!confirm(`确定要删除任务 "${props.currentTaskId}" 吗？`)) return;
  emit("delete-task", props.currentTaskId);
}
</script>

<template>
  <!-- 折叠时只显示 tab -->
  <div
    v-if="collapsed"
    class="fixed left-0 top-1/3 z-40 cursor-pointer"
    @click="collapsed = false"
  >
    <div
      class="flex flex-col items-center justify-center gap-1.5 px-2 py-4 bg-card border-(length:--theme-border-width) border-l-0 border-border rounded-r-(--theme-radius) shadow-card hover:shadow-card-hover transition-all"
    >
      <svg class="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
      <span
        class="text-[10px] font-display font-semibold text-muted-foreground uppercase tracking-wider"
        style="writing-mode: vertical-rl; text-orientation: mixed;"
      >任务</span>
      <svg class="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </div>
  </div>

  <!-- 展开面板 -->
  <Transition name="panel-left">
    <div
      v-if="!collapsed"
      class="fixed left-4 top-20 z-40 w-72 flex flex-col bg-card/95 backdrop-blur border-(length:--theme-border-width) border-border rounded-(--theme-radius) shadow-card-hover overflow-hidden max-h-[calc(100vh-6.5rem)]"
    >
      <!-- Panel Header -->
      <div class="flex items-center gap-2 px-4 py-3 border-b border-border shrink-0">
        <svg class="w-4 h-4 text-primary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <span class="flex-1 text-xs font-display font-semibold text-foreground uppercase tracking-wider">任务列表</span>
        <!-- 创建任务按钮 -->
        <button
          @click="showCreateModal = true"
          class="p-1 rounded text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          title="创建任务"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <!-- 折叠按钮 -->
        <button
          @click="collapsed = true"
          class="p-1 rounded text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          title="收起"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </div>

      <!-- Task List -->
      <div class="flex-1 min-h-0 overflow-y-auto">
        <div class="flex items-center justify-between px-4 py-2">
          <span class="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider">
            {{ tasks.length }} 个任务
          </span>
          <button
            @click="$emit('refresh-tasks')"
            class="text-[10px] font-semibold text-primary hover:underline"
          >
            刷新
          </button>
        </div>

        <div v-if="tasks.length === 0" class="px-4 py-6 text-center text-sm text-muted-foreground">
          暂无任务
        </div>

        <button
          v-for="task in tasks"
          :key="task.task_id"
          @click="selectTask(task.task_id)"
          class="w-full px-4 py-3 text-left hover:bg-muted transition-colors flex items-start gap-3"
          :class="{ 'bg-primary/10': task.task_id === currentTaskId }"
        >
          <span
            class="status-dot mt-1.5 shrink-0"
            :class="task.status?.state === 'running' ? 'status-running' : 'status-idle'"
          ></span>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-semibold text-foreground truncate">
              {{ task.config?.name || task.task_id }}
            </div>
            <div class="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5">
              <span>{{ task.status?.state || 'unknown' }}</span>
              <span v-if="task.config?.name" class="font-mono opacity-60 truncate max-w-[100px]">· {{ task.task_id }}</span>
            </div>
          </div>
          <svg v-if="task.task_id === currentTaskId" class="w-4 h-4 text-primary shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </button>
      </div>

      <!-- Task Actions -->
      <div
        v-if="canDelete"
        class="px-3 py-3 border-t border-border shrink-0"
      >
        <div class="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider px-1 mb-2">
          当前任务：<span class="font-mono text-foreground">{{ currentTaskId }}</span>
        </div>
        <Button
          variant="destructive"
          size="sm"
          class="w-full"
          @click="deleteTask"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          删除任务
        </Button>
      </div>
    </div>
  </Transition>

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
      <div>
        <label class="block text-xs font-display font-semibold text-muted-foreground mb-2 uppercase tracking-wider">
          任务名称 <span class="text-destructive">*</span>
        </label>
        <Input v-model="createForm.name" placeholder="为任务起一个易识别的名称" />
      </div>

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
        <label class="block text-xs font-display font-semibold text-muted-foreground mb-2 uppercase tracking-wider">描述</label>
        <textarea
          v-model="createForm.description"
          placeholder="任务用途说明（选填）"
          rows="2"
          class="w-full px-3 py-2 text-sm bg-background border-(length:--theme-border-width) border-border rounded-(--theme-radius) text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
        ></textarea>
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
      <Button variant="ghost" @click="showCreateModal = false">取消</Button>
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
</template>

<style scoped>
.panel-left-enter-active,
.panel-left-leave-active {
  transition: all 0.25s ease;
}
.panel-left-enter-from,
.panel-left-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}
</style>
