<script setup lang="ts">
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center font-display font-semibold text-xs px-2.5 py-0.5 border-(length:--theme-border-width) border-border rounded-(--theme-radius) transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow-[2px_2px_0px_var(--theme-border)]",
        secondary: "bg-secondary text-secondary-foreground shadow-[2px_2px_0px_var(--theme-border)]",
        outline: "bg-background text-foreground",
        destructive: "bg-destructive text-white shadow-[2px_2px_0px_var(--theme-border)]",
        success: "bg-[#00ff88] text-[#1a1a1a] shadow-[2px_2px_0px_var(--theme-border)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

type BadgeVariants = VariantProps<typeof badgeVariants>;

const props = defineProps<{
  variant?: NonNullable<BadgeVariants["variant"]>;
  class?: string;
}>();
</script>

<template>
  <span :class="cn(badgeVariants({ variant }), props.class)">
    <slot />
  </span>
</template>
