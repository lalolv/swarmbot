<script setup lang="ts">
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const alertVariants = cva(
  "flex items-start gap-3 p-4 border-(length:--theme-border-width) border-border rounded-(--theme-radius) shadow-card",
  {
    variants: {
      variant: {
        default: "bg-card text-card-foreground",
        destructive: "bg-destructive/10 text-destructive border-destructive",
        success: "bg-[#00ff88]/10 text-foreground border-[#00ff88]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

type AlertVariants = VariantProps<typeof alertVariants>;

const props = defineProps<{
  variant?: NonNullable<AlertVariants["variant"]>;
  class?: string;
}>();
</script>

<template>
  <div :class="cn(alertVariants({ variant }), props.class)">
    <slot />
  </div>
</template>
