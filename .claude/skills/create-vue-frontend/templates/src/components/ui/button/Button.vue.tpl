<script setup lang="ts">
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 font-display font-semibold text-sm transition-all active:translate-y-0.5 disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground border-(length:--theme-border-width) border-border rounded-(--theme-radius) shadow-card hover:shadow-card-hover hover:-translate-y-0.5 active:shadow-none",
        secondary:
          "bg-secondary text-secondary-foreground border-(length:--theme-border-width) border-border rounded-(--theme-radius) shadow-card hover:shadow-card-hover hover:-translate-y-0.5 active:shadow-none",
        destructive:
          "bg-destructive text-white border-(length:--theme-border-width) border-border rounded-(--theme-radius) shadow-card hover:shadow-card-hover hover:-translate-y-0.5 active:shadow-none",
        outline:
          "bg-background text-foreground border-(length:--theme-border-width) border-border rounded-(--theme-radius) shadow-card hover:shadow-card-hover hover:-translate-y-0.5 active:shadow-none",
        ghost:
          "bg-transparent text-foreground rounded-(--theme-radius) hover:bg-muted",
        link:
          "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-6 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

type ButtonVariants = VariantProps<typeof buttonVariants>;

const props = defineProps<{
  variant?: NonNullable<ButtonVariants["variant"]>;
  size?: NonNullable<ButtonVariants["size"]>;
  class?: string;
  disabled?: boolean;
}>();
</script>

<template>
  <button
    :class="cn(buttonVariants({ variant, size }), props.class)"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>
