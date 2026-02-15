<script setup lang="ts">
import { cn } from "@/lib/utils";

const props = defineProps<{
  class?: string;
}>();
</script>

<template>
  <div :class="cn('px-6 py-4 border-t border-border flex items-center justify-end gap-3', props.class)">
    <slot />
  </div>
</template>
