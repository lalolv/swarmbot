<script setup lang="ts">
import { cn } from "@/lib/utils";
import type { ClassValue } from "clsx";

const props = defineProps<{
  class?: ClassValue;
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
