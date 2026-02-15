<script setup lang="ts">
import { ref } from "vue";
import { cn } from "@/lib/utils";

const props = defineProps<{
  text: string;
  class?: string;
}>();

const show = ref(false);
</script>

<template>
  <div class="relative inline-flex" @mouseenter="show = true" @mouseleave="show = false">
    <slot />
    <Transition name="tooltip">
      <div
        v-if="show"
        :class="cn(
          'absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2.5 py-1 text-xs font-medium whitespace-nowrap bg-foreground text-background border-(length:--theme-border-width) border-border rounded-(--theme-radius) shadow-card z-50 pointer-events-none',
          props.class
        )"
      >
        {{ text }}
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.tooltip-enter-active,
.tooltip-leave-active {
  transition: opacity 0.1s ease;
}
.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
}
</style>
