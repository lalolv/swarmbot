<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const open = defineModel<boolean>("open", { default: false });

const props = withDefaults(
  defineProps<{
    panelId?: string;
    panelClass?: string;
    autoFocusFirst?: boolean;
    closeOnOutside?: boolean;
    closeOnEscape?: boolean;
    restoreFocus?: boolean;
  }>(),
  {
    panelId: undefined,
    panelClass: "",
    autoFocusFirst: true,
    closeOnOutside: true,
    closeOnEscape: true,
    restoreFocus: true,
  }
);

const rootRef = ref<HTMLElement | null>(null);
const panelRef = ref<HTMLElement | null>(null);
const triggerRef = ref<HTMLElement | null>(null);

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
      :class="panelClass"
    >
      <slot :open="open" :close="close" />
    </div>
  </div>
</template>
