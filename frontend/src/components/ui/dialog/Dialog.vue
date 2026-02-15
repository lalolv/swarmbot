<script setup lang="ts">
import { cn } from "@/lib/utils";

defineProps<{
  open: boolean;
  class?: string;
}>();

const emit = defineEmits<{
  close: [];
}>();

function onOverlayClick(e: MouseEvent) {
  if (e.target === e.currentTarget) {
    emit("close");
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div
        v-if="open"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/40"
        @click="onOverlayClick"
      >
        <div
          :class="cn(
            'w-full max-w-lg bg-card text-card-foreground border-(length:--theme-border-width) border-border rounded-(--theme-radius) shadow-card-hover animate-fade-in overflow-hidden',
            $props.class
          )"
        >
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-enter-active,
.dialog-leave-active {
  transition: opacity 0.15s ease;
}
.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}
</style>
