<script setup lang="ts">
import { cn } from "@/lib/utils";

const props = defineProps<{
  class?: string;
  modelValue?: string | number;
}>();

defineEmits<{
  "update:modelValue": [value: string];
}>();
</script>

<template>
  <input
    :class="cn(
      'w-full h-10 px-3 text-sm bg-background text-foreground border-(length:--theme-border-width) border-border rounded-(--theme-radius) outline-none transition-all placeholder:text-muted-foreground focus:ring-2 focus:ring-ring focus:ring-offset-1',
      props.class
    )"
    :value="modelValue"
    @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
  />
</template>
