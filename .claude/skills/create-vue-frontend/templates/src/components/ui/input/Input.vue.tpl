<script setup lang="ts">
import { cn } from "@/lib/utils";

const props = defineProps<{
  class?: string;
  placeholder?: string;
  modelValue?: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();
</script>

<template>
  <input
    :value="props.modelValue"
    @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    :placeholder="props.placeholder"
    :class="cn(
      'w-full h-10 px-3 py-2 text-sm font-body bg-background text-foreground',
      'border-(length:--theme-border-width) border-border rounded-(--theme-radius)',
      'placeholder:text-muted-foreground',
      'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-0',
      'transition-all',
      props.class
    )"
  />
</template>
