<script setup lang="ts">
import { cn } from "@/lib/utils";

const props = defineProps<{
  class?: string;
}>();
</script>

<template>
  <div :class="cn(
    'bg-card text-card-foreground border-(length:--theme-border-width) border-border rounded-(--theme-radius) shadow-card transition-shadow',
    props.class
  )">
    <slot />
  </div>
</template>
