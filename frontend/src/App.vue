<script setup>
import { computed, onBeforeUnmount, onMounted } from "vue";

import Header from "./components/Header.vue";
import InfiniteCanvas from "./components/InfiniteCanvas.vue";
import { useObservabilityStore } from "./stores/observability";

const store = useObservabilityStore();

// Computed
const isSubscribed = computed(() => store.connectionState === "connected" || store.connectionState === "connecting");

// Methods
async function handleCreateTask(form) {
  await store.createNewTask(form);
}

async function handleSelectTask(taskId) {
  store.monitorTaskId = taskId;
  // Unsubscribe from current task if subscribed
  if (isSubscribed.value) {
    store.stopMonitoring();
  }
}

async function handleSubscribe(taskId) {
  await store.startMonitoring(taskId);
}

function handleUnsubscribe() {
  store.stopMonitoring();
}

async function handleDeleteTask(taskId) {
  await store.cleanupTask(taskId);
}

async function handleRefreshTasks() {
  await store.refreshTasks();
}

// Lifecycle
onMounted(() => {
  store.initialize();
});

onBeforeUnmount(() => {
  store.stopMonitoring();
});
</script>

<template>
  <div class="relative w-full h-full overflow-hidden bg-void">
    <!-- Animated background -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <!-- Gradient orbs -->
      <div class="absolute -top-1/4 -left-1/4 w-[800px] h-[800px] rounded-full bg-neon-cyan/5 blur-[150px]"></div>
      <div class="absolute -bottom-1/4 -right-1/4 w-[600px] h-[600px] rounded-full bg-neon-purple/5 blur-[120px]"></div>
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] rounded-full bg-neon-pink/3 blur-[200px]"></div>
      
      <!-- Grid overlay -->
      <div class="absolute inset-0 opacity-30" 
           style="background-image: linear-gradient(rgba(0, 240, 255, 0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 240, 255, 0.02) 1px, transparent 1px); background-size: 100px 100px;">
      </div>
    </div>

    <!-- Header -->
    <Header
      :tasks="store.tasks"
      :robot-types="store.robotTypes"
      :current-task-id="store.monitorTaskId"
      :is-subscribed="isSubscribed"
      :connection-state="store.connectionState"
      @create-task="handleCreateTask"
      @select-task="handleSelectTask"
      @subscribe="handleSubscribe"
      @unsubscribe="handleUnsubscribe"
      @delete-task="handleDeleteTask"
      @refresh-tasks="handleRefreshTasks"
    />

    <!-- Main Content - Infinite Canvas -->
    <main class="absolute inset-0 pt-16">
      <InfiniteCanvas
        :robots="store.robotList"
        :task-id="store.monitorTaskId"
        :task-state="store.taskState"
      />
    </main>

    <!-- Toast Notification -->
    <Transition name="toast">
      <div v-if="store.lastError" 
           class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-6 py-3 rounded-xl bg-neon-pink/20 border border-neon-pink/30 backdrop-blur-xl">
        <div class="flex items-center gap-3">
          <svg class="w-5 h-5 text-neon-pink" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="text-sm text-white">{{ store.lastError }}</span>
          <button @click="store.lastError = ''" class="ml-2 text-slate-400 hover:text-white">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* Toast animation */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

/* Smooth transitions */
* {
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
