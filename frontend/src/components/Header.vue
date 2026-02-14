<script setup>
import { computed, reactive, ref } from "vue";

const props = defineProps({
  tasks: {
    type: Array,
    default: () => [],
  },
  robotTypes: {
    type: Array,
    default: () => [],
  },
  currentTaskId: {
    type: String,
    default: "",
  },
  isSubscribed: {
    type: Boolean,
    default: false,
  },
  connectionState: {
    type: String,
    default: "idle",
  },
});

const emit = defineEmits([
  "create-task",
  "select-task",
  "subscribe",
  "unsubscribe",
  "delete-task",
  "refresh-tasks",
]);

// Create task modal
const showCreateModal = ref(false);
const creating = ref(false);
const createForm = reactive({
  taskId: "",
  userId: "",
  pollInterval: 2,
  selectedRobots: [],
});

// Task list dropdown
const showTaskList = ref(false);

// Computed
const canSubscribe = computed(() => props.currentTaskId && !props.isSubscribed);
const canUnsubscribe = computed(() => props.isSubscribed);
const canDelete = computed(() => props.currentTaskId);

const connectionStatusColor = computed(() => {
  switch (props.connectionState) {
    case "connected":
      return "bg-neon-green";
    case "connecting":
      return "bg-neon-yellow";
    case "error":
    case "closed":
      return "bg-neon-pink";
    default:
      return "bg-slate-500";
  }
});

// Methods
function toggleRobot(robotType) {
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
    await emit("create-task", { ...createForm });
    showCreateModal.value = false;
    createForm.taskId = "";
    createForm.userId = "";
    createForm.selectedRobots = [];
  } finally {
    creating.value = false;
  }
}

function selectTask(taskId) {
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
  <header class="fixed top-0 left-0 right-0 z-50 h-16 glass-strong">
    <div class="h-full px-4 flex items-center justify-between">
      <!-- Logo & Title -->
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-neon-cyan to-neon-purple flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <div>
            <h1 class="font-display text-lg font-semibold gradient-text">PM Sports Bots</h1>
            <p class="text-[10px] text-slate-400 tracking-wider uppercase">Task Orchestration System</p>
          </div>
        </div>
        
        <!-- Connection Status -->
        <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface border border-white/5">
          <span class="w-2 h-2 rounded-full" :class="connectionStatusColor"></span>
          <span class="text-xs text-slate-400 capitalize">{{ connectionState }}</span>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-2">
        <!-- Create Task Button -->
        <button
          @click="showCreateModal = true"
          class="btn-primary flex items-center gap-2 text-sm text-neon-cyan"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span class="hidden sm:inline">创建任务</span>
        </button>

        <!-- Task List Dropdown -->
        <div class="relative">
          <button
            @click="showTaskList = !showTaskList"
            class="px-4 py-2 rounded-lg bg-surface border border-white/10 text-sm font-medium text-slate-300 hover:border-neon-cyan/30 transition-all flex items-center gap-2"
          >
            <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <span class="hidden sm:inline max-w-[120px] truncate">
              {{ currentTaskId || '选择任务' }}
            </span>
            <svg class="w-4 h-4 text-slate-500" :class="{ 'rotate-180': showTaskList }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Task List Dropdown Menu -->
          <div v-if="showTaskList" 
               class="absolute top-full right-0 mt-2 w-72 glass-strong rounded-xl overflow-hidden animate-slide-down">
            <div class="p-3 border-b border-white/5 flex items-center justify-between">
              <span class="text-xs font-medium text-slate-400 uppercase tracking-wider">任务列表</span>
              <button @click="$emit('refresh-tasks')" class="text-xs text-neon-cyan hover:underline">
                刷新
              </button>
            </div>
            <div class="max-h-64 overflow-y-auto">
              <div v-if="tasks.length === 0" class="p-4 text-center text-sm text-slate-500">
                暂无任务
              </div>
              <button
                v-for="task in tasks"
                :key="task.task_id"
                @click="selectTask(task.task_id)"
                class="w-full px-4 py-3 text-left hover:bg-white/5 transition-colors flex items-center gap-3"
                :class="{ 'bg-neon-cyan/10': task.task_id === currentTaskId }"
              >
                <span class="w-2 h-2 rounded-full" 
                      :class="task.status?.state === 'running' ? 'bg-neon-green' : 'bg-slate-500'"></span>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-slate-200 truncate">{{ task.task_id }}</div>
                  <div class="text-xs text-slate-500">{{ task.status?.state || 'unknown' }}</div>
                </div>
                <svg v-if="task.task_id === currentTaskId" class="w-4 h-4 text-neon-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Subscribe Toggle -->
        <button
          v-if="canSubscribe"
          @click="toggleSubscription"
          class="btn-primary flex items-center gap-2 text-sm text-neon-green"
          :disabled="!currentTaskId"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <span class="hidden sm:inline">订阅</span>
        </button>

        <button
          v-else-if="canUnsubscribe"
          @click="toggleSubscription"
          class="px-4 py-2 rounded-lg bg-surface border border-neon-pink/30 text-sm font-medium text-neon-pink hover:bg-neon-pink/10 transition-all flex items-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <span class="hidden sm:inline">取消订阅</span>
        </button>

        <!-- Delete Task -->
        <button
          v-if="canDelete"
          @click="deleteTask"
          class="btn-danger flex items-center gap-2 text-sm"
          title="删除任务"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          <span class="hidden sm:inline">删除</span>
        </button>
      </div>
    </div>

    <!-- Create Task Modal -->
    <div v-if="showCreateModal" 
         class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
         @click.self="showCreateModal = false">
      <div class="w-full max-w-lg glass-strong rounded-2xl overflow-hidden animate-fade-in">
        <!-- Modal Header -->
        <div class="px-6 py-4 border-b border-white/5 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-neon-cyan/20 to-neon-purple/20 flex items-center justify-center">
              <svg class="w-5 h-5 text-neon-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
            </div>
            <div>
              <h3 class="font-display text-lg font-semibold text-white">创建新任务</h3>
              <p class="text-xs text-slate-400">配置任务参数并选择机器人</p>
            </div>
          </div>
          <button @click="showCreateModal = false" class="text-slate-400 hover:text-white transition-colors">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Modal Body -->
        <div class="p-6 space-y-5">
          <!-- Task ID & User ID -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-2 uppercase tracking-wider">任务 ID</label>
              <input
                v-model="createForm.taskId"
                type="text"
                placeholder="自动生成"
                class="input-field"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-2 uppercase tracking-wider">用户 ID</label>
              <input
                v-model="createForm.userId"
                type="text"
                placeholder="可选"
                class="input-field"
              />
            </div>
          </div>

          <!-- Poll Interval -->
          <div>
            <label class="block text-xs font-medium text-slate-400 mb-2 uppercase tracking-wider">
              轮询间隔 (秒)
            </label>
            <div class="flex items-center gap-4">
              <input
                v-model.number="createForm.pollInterval"
                type="range"
                min="0.2"
                max="10"
                step="0.1"
                class="flex-1 h-2 bg-surface rounded-lg appearance-none cursor-pointer accent-neon-cyan"
              />
              <span class="w-16 text-right font-mono text-sm text-neon-cyan">{{ createForm.pollInterval }}s</span>
            </div>
          </div>

          <!-- Robot Selection -->
          <div>
            <label class="block text-xs font-medium text-slate-400 mb-3 uppercase tracking-wider">
              选择机器人 <span class="text-neon-pink">*</span>
            </label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="robotType in robotTypes"
                :key="robotType"
                @click="toggleRobot(robotType)"
                class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all border"
                :class="createForm.selectedRobots.includes(robotType)
                  ? 'bg-neon-cyan/20 border-neon-cyan/50 text-neon-cyan'
                  : 'bg-surface border-white/10 text-slate-400 hover:border-white/20'"
              >
                {{ robotType }}
              </button>
            </div>
            <p v-if="createForm.selectedRobots.length === 0" class="mt-2 text-xs text-neon-pink">
              请至少选择一个机器人
            </p>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="px-6 py-4 border-t border-white/5 flex items-center justify-end gap-3">
          <button
            @click="showCreateModal = false"
            class="px-4 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition-colors"
          >
            取消
          </button>
          <button
            @click="submitCreate"
            :disabled="creating || createForm.selectedRobots.length === 0"
            class="btn-primary flex items-center gap-2"
            :class="{ 'opacity-50 cursor-not-allowed': creating || createForm.selectedRobots.length === 0 }"
          >
            <svg v-if="creating" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            <span>{{ creating ? '创建中...' : '创建任务' }}</span>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
/* Click outside to close dropdowns */
header {
  isolation: isolate;
}
</style>
