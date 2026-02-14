<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from "vue";

import CanvasTopology from "./components/CanvasTopology.vue";
import { useObservabilityStore } from "./stores/observability";

const store = useObservabilityStore();

const form = reactive({
  taskId: "",
  userId: "",
  pollInterval: 2,
  selectedRobots: [],
});

const loading = ref(false);
const creating = ref(false);
const syncing = ref(false);
const stopping = ref(false);
const cleaning = ref(false);
const message = ref("");

function toggleRobot(robotType) {
  if (form.selectedRobots.includes(robotType)) {
    form.selectedRobots = form.selectedRobots.filter((item) => item !== robotType);
    return;
  }
  form.selectedRobots.push(robotType);
}

async function initialize() {
  loading.value = true;
  message.value = "";
  try {
    await store.initialize();
    if (store.monitorTaskId) {
      await store.startMonitoring(store.monitorTaskId);
    }
  } catch (error) {
    message.value = error.message;
  } finally {
    loading.value = false;
  }
}

async function submitCreate() {
  creating.value = true;
  message.value = "";
  try {
    const result = await store.createNewTask(form);
    message.value = `任务创建成功: ${result.task_id}`;
    form.taskId = "";
    form.userId = "";
  } catch (error) {
    message.value = error.message;
  } finally {
    creating.value = false;
  }
}

async function monitorSelected() {
  message.value = "";
  try {
    await store.startMonitoring(store.monitorTaskId);
  } catch (error) {
    message.value = error.message;
  }
}

async function syncTask() {
  syncing.value = true;
  message.value = "";
  try {
    await store.syncTaskRobots(store.monitorTaskId);
    message.value = `同步完成: ${store.monitorTaskId}`;
  } catch (error) {
    message.value = error.message;
  } finally {
    syncing.value = false;
  }
}

async function stopTask() {
  stopping.value = true;
  message.value = "";
  try {
    const result = await store.stopTask(store.monitorTaskId);
    message.value = result?.message || `任务已停止: ${store.monitorTaskId}`;
  } catch (error) {
    message.value = error.message;
  } finally {
    stopping.value = false;
  }
}

async function cleanupTask() {
  cleaning.value = true;
  message.value = "";
  try {
    const taskId = store.monitorTaskId;
    const result = await store.cleanupTask(taskId);
    message.value = result?.message || `任务已清理: ${taskId}`;
  } catch (error) {
    message.value = error.message;
  } finally {
    cleaning.value = false;
  }
}

onMounted(() => {
  initialize();
});

onBeforeUnmount(() => {
  store.stopMonitoring();
});
</script>

<template>
  <div class="min-h-screen bg-app px-4 py-6 text-ink md:px-8">
    <div class="mx-auto max-w-[1400px] space-y-4">
      <header class="rounded-3xl bg-white/85 p-5 shadow-panel backdrop-blur animate-floatIn">
        <p class="font-body text-xs uppercase tracking-[0.25em] text-slate-500">PM Sports Bots</p>
        <h1 class="mt-1 font-display text-3xl">Create Task + Infinite Canvas Monitor</h1>
        <p class="mt-2 text-sm text-slate-600">仅保留两个核心功能：任务创建、无限画布监控。</p>
      </header>

      <section class="grid gap-4 xl:grid-cols-[420px_1fr]">
        <aside class="rounded-3xl bg-white/85 p-5 shadow-panel backdrop-blur">
          <h2 class="font-display text-xl">Create Task</h2>

          <form class="mt-4 space-y-3" @submit.prevent="submitCreate">
            <label class="block">
              <span class="mb-1 block text-xs text-slate-500">task_id (optional)</span>
              <input
                v-model="form.taskId"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky"
                placeholder="demo-task-1"
              />
            </label>

            <label class="block">
              <span class="mb-1 block text-xs text-slate-500">user_id (optional)</span>
              <input
                v-model="form.userId"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky"
                placeholder="u1"
              />
            </label>

            <label class="block">
              <span class="mb-1 block text-xs text-slate-500">poll_interval</span>
              <input
                v-model.number="form.pollInterval"
                type="number"
                min="0.2"
                step="0.1"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky"
              />
            </label>

            <div>
              <p class="mb-2 text-xs text-slate-500">robots</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="robotType in store.robotTypes"
                  :key="robotType"
                  type="button"
                  class="rounded-full border px-3 py-1 text-xs transition"
                  :class="form.selectedRobots.includes(robotType)
                    ? 'border-sky bg-sky/10 text-sky-700'
                    : 'border-slate-300 bg-white text-slate-600 hover:border-slate-400'"
                  @click="toggleRobot(robotType)"
                >
                  {{ robotType }}
                </button>
              </div>
            </div>

            <button
              class="w-full rounded-xl bg-ink px-3 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-50"
              :disabled="creating"
              type="submit"
            >
              {{ creating ? 'Creating...' : 'Create & Monitor' }}
            </button>
          </form>

          <div class="mt-6 border-t border-slate-200 pt-4">
            <h3 class="font-display text-lg">Monitor Task</h3>
            <div class="mt-2 flex gap-2">
              <select
                v-model="store.monitorTaskId"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky"
              >
                <option value="">Select task</option>
                <option v-for="task in store.tasks" :key="task.task_id" :value="task.task_id">
                  {{ task.task_id }}
                </option>
              </select>
              <button
                class="rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:border-slate-500"
                @click="monitorSelected"
              >
                Start
              </button>
              <button
                class="rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:border-slate-500 disabled:opacity-50"
                :disabled="syncing || !store.monitorTaskId"
                @click="syncTask"
              >
                {{ syncing ? 'Syncing...' : 'Sync' }}
              </button>
            </div>
            <div class="mt-2 grid grid-cols-2 gap-2">
              <button
                class="rounded-xl border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-700 hover:border-amber-400 disabled:opacity-50"
                :disabled="stopping || !store.monitorTaskId"
                @click="stopTask"
              >
                {{ stopping ? 'Stopping...' : 'Stop Task' }}
              </button>
              <button
                class="rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700 hover:border-rose-400 disabled:opacity-50"
                :disabled="cleaning || !store.monitorTaskId"
                @click="cleanupTask"
              >
                {{ cleaning ? 'Cleaning...' : 'Cleanup Task' }}
              </button>
            </div>
          </div>

          <p v-if="message" class="mt-3 rounded-xl bg-slate-100 px-3 py-2 text-xs text-slate-700">{{ message }}</p>
          <p v-if="store.lastError" class="mt-3 rounded-xl bg-rose-50 px-3 py-2 text-xs text-rose-700">{{ store.lastError }}</p>
          <p v-if="loading" class="mt-3 text-xs text-slate-500">Loading...</p>
        </aside>

        <section class="space-y-3">
          <div class="grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
            <article class="rounded-2xl bg-white/85 p-3 shadow-panel backdrop-blur">
              <p class="text-[11px] uppercase text-slate-500">task</p>
              <p class="mt-1 truncate font-display text-sm">{{ store.monitorTaskId || '-' }}</p>
            </article>
            <article class="rounded-2xl bg-white/85 p-3 shadow-panel backdrop-blur">
              <p class="text-[11px] uppercase text-slate-500">task state</p>
              <p class="mt-1 font-display text-sm">{{ store.taskState }}</p>
            </article>
            <article class="rounded-2xl bg-white/85 p-3 shadow-panel backdrop-blur">
              <p class="text-[11px] uppercase text-slate-500">stream</p>
              <p class="mt-1 font-display text-sm">{{ store.connectionState }}</p>
            </article>
            <article class="rounded-2xl bg-white/85 p-3 shadow-panel backdrop-blur">
              <p class="text-[11px] uppercase text-slate-500">robots</p>
              <p class="mt-1 font-display text-sm">{{ store.robotList.length }}</p>
            </article>
            <article class="rounded-2xl bg-white/85 p-3 shadow-panel backdrop-blur">
              <p class="text-[11px] uppercase text-slate-500">events</p>
              <p class="mt-1 font-display text-sm">{{ store.eventCount }}</p>
            </article>
          </div>

          <CanvasTopology
            :task-id="store.monitorTaskId"
            :task-state="store.taskState"
            :connection-state="store.connectionState"
            :robots="store.robotList"
            :event-count="store.eventCount"
          />
        </section>
      </section>
    </div>
  </div>
</template>
