<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { cn } from "@/lib/utils";

const open = defineModel<boolean>("open", { default: false });

const props = withDefaults(
  defineProps<{
    panelId?: string;
    panelClass?: string;
    placement?: "bottom-start" | "bottom-end";
    offset?: "none" | "sm" | "md" | "lg";
    autoFocusFirst?: boolean;
    closeOnOutside?: boolean;
    closeOnEscape?: boolean;
    restoreFocus?: boolean;
  }>(),
  {
    panelId: undefined,
    panelClass: "",
    placement: "bottom-end",
    offset: "md",
    autoFocusFirst: true,
    closeOnOutside: true,
    closeOnEscape: true,
    restoreFocus: true,
  }
);

const rootRef = ref<HTMLElement | null>(null);
const panelRef = ref<HTMLElement | null>(null);
const triggerRef = ref<HTMLElement | null>(null);

const panelOffsetClass = computed(() => {
  if (props.offset === "none") {
    return "mt-0";
  }
  if (props.offset === "sm") {
    return "mt-1.5";
  }
  if (props.offset === "lg") {
    return "mt-3";
  }
  return "mt-2";
});

const panelPlacementClass = computed(() => {
  if (props.placement === "bottom-start") {
    return "absolute left-0 top-full";
  }
  return "absolute right-0 top-full";
});

function close(restoreFocus = props.restoreFocus) {
  if (!open.value) {
    return;
  }
  open.value = false;
  if (restoreFocus) {
    triggerRef.value?.focus();
  }
}

function toggle() {
  open.value = !open.value;
}

function handleClickOutside(event: MouseEvent) {
  if (!props.closeOnOutside || !open.value || !rootRef.value) {
    return;
  }

  const target = event.target;
  if (target instanceof Node && !rootRef.value.contains(target)) {
    close(false);
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (!props.closeOnEscape || !open.value) {
    return;
  }

  if (event.key === "Escape") {
    event.preventDefault();
    close();
  }
}

watch(open, async (isOpen) => {
  if (!isOpen || !props.autoFocusFirst) {
    return;
  }

  await nextTick();
  const firstFocusable = panelRef.value?.querySelector<HTMLElement>(
    "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
  );
  firstFocusable?.focus();
});

onMounted(() => {
  document.addEventListener("mousedown", handleClickOutside);
  document.addEventListener("keydown", handleKeydown);
});

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", handleClickOutside);
  document.removeEventListener("keydown", handleKeydown);
});
</script>

<template>
  <div ref="rootRef" class="relative">
    <div ref="triggerRef">
      <slot name="trigger" :open="open" :toggle="toggle" :close="close" />
    </div>

    <div
      v-if="open"
      :id="panelId"
      ref="panelRef"
      tabindex="-1"
      :class="cn(panelPlacementClass, panelOffsetClass, panelClass)"
    >
      <slot :open="open" :close="close" />
    </div>
  </div>
</template>
