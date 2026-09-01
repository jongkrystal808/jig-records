<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    open: boolean;
    labelledBy: string;
    describedBy?: string;
    dialogRole?: "dialog" | "alertdialog";
    layerClass?: string;
    dialogClass?: string;
    closeOnBackdrop?: boolean;
  }>(),
  {
    describedBy: undefined,
    dialogRole: "dialog",
    layerClass: "",
    dialogClass: "",
    closeOnBackdrop: true
  }
);

const emit = defineEmits<{
  close: [];
}>();

const layerRef = ref<HTMLElement | null>(null);
const dialogRef = ref<HTMLElement | null>(null);
const inertedSiblings: Array<{ element: HTMLElement; wasInert: boolean }> = [];
let returnFocusTarget: HTMLElement | null = null;

const focusableSelector = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled]):not([type='hidden'])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])"
].join(",");

function isTopModal(): boolean {
  const openDialogs = Array.from(document.body.querySelectorAll<HTMLElement>("[aria-modal='true']"));
  return openDialogs.at(-1) === dialogRef.value;
}

function setBackgroundInert(): void {
  const layer = layerRef.value;
  if (!layer) return;
  inertedSiblings.length = 0;
  for (const child of Array.from(document.body.children)) {
    if (!(child instanceof HTMLElement) || child === layer) continue;
    inertedSiblings.push({ element: child, wasInert: child.hasAttribute("inert") });
    child.setAttribute("inert", "");
  }
}

function restoreBackground(): void {
  for (const { element, wasInert } of inertedSiblings.splice(0)) {
    if (!wasInert) {
      element.removeAttribute("inert");
    }
  }
}

function focusInitialControl(): void {
  const dialog = dialogRef.value;
  if (!dialog) return;
  const preferred = dialog.querySelector<HTMLElement>("[data-modal-initial-focus]");
  const firstControl = dialog.querySelector<HTMLElement>(focusableSelector);
  (preferred ?? firstControl ?? dialog).focus();
}

function focusableControls(): HTMLElement[] {
  return dialogRef.value
    ? Array.from(dialogRef.value.querySelectorAll<HTMLElement>(focusableSelector))
    : [];
}

function handleDocumentKeydown(event: KeyboardEvent): void {
  if (!props.open || !isTopModal()) return;
  if (event.key === "Escape") {
    event.preventDefault();
    emit("close");
    return;
  }
  if (event.key !== "Tab") return;

  const controls = focusableControls();
  if (controls.length === 0) {
    event.preventDefault();
    dialogRef.value?.focus();
    return;
  }
  const first = controls[0];
  const last = controls[controls.length - 1];
  const active = document.activeElement;
  if (!dialogRef.value?.contains(active)) {
    event.preventDefault();
    (event.shiftKey ? last : first).focus();
    return;
  }
  if ((event.shiftKey && active === first) || (!event.shiftKey && active === last)) {
    event.preventDefault();
    (event.shiftKey ? last : first).focus();
  }
}

function handleBackdropClick(): void {
  if (props.closeOnBackdrop && isTopModal()) {
    emit("close");
  }
}

async function activateModal(): Promise<void> {
  returnFocusTarget = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  document.addEventListener("keydown", handleDocumentKeydown);
  await nextTick();
  if (!props.open) return;
  setBackgroundInert();
  focusInitialControl();
}

async function deactivateModal(): Promise<void> {
  document.removeEventListener("keydown", handleDocumentKeydown);
  restoreBackground();
  await nextTick();
  if (returnFocusTarget?.isConnected) {
    returnFocusTarget.focus();
  }
  returnFocusTarget = null;
}

watch(
  () => props.open,
  (open) => {
    if (open) {
      void activateModal();
    } else {
      void deactivateModal();
    }
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  document.removeEventListener("keydown", handleDocumentKeydown);
  restoreBackground();
  if (returnFocusTarget?.isConnected) {
    returnFocusTarget.focus();
  }
});
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      ref="layerRef"
      class="ui-modal-backdrop"
      :class="layerClass"
      role="presentation"
      @click.self="handleBackdropClick"
    >
      <section
        ref="dialogRef"
        class="ui-modal-card"
        :class="dialogClass"
        :role="dialogRole"
        aria-modal="true"
        :aria-labelledby="labelledBy"
        :aria-describedby="describedBy"
        tabindex="-1"
        @keydown.stop="handleDocumentKeydown"
      >
        <slot />
      </section>
    </div>
  </Teleport>
</template>
