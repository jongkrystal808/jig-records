<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

interface GuidedTourStepNote {
  tone: "warning" | "info";
  text: string;
}

interface GuidedTourStepExample {
  label?: string;
  value: string;
}

interface GuidedTourStepImage {
  src: string;
  alt: string;
}

interface GuidedTourStep {
  id: string;
  target: string;
  title: string;
  description: string;
  bullets?: string[];
  example?: GuidedTourStepExample[];
  note?: GuidedTourStepNote;
  image?: GuidedTourStepImage;
  placement?: "top" | "bottom" | "left" | "right";
}

const props = defineProps<{
  open: boolean;
  steps: GuidedTourStep[];
  currentIndex: number;
  flowLabel?: string;
  flowSectionLabel?: string;
}>();

const emit = defineEmits<{
  close: [];
  next: [];
  prev: [];
}>();

const spotlightRect = ref<DOMRect | null>(null);
const cardStyle = ref<Record<string, string>>({});
const tourCardRef = ref<HTMLElement | null>(null);
let retryTimer: ReturnType<typeof setTimeout> | null = null;
let retryCount = 0;

const currentStep = computed(() => props.steps[props.currentIndex] ?? null);
const isFirstStep = computed(() => props.currentIndex <= 0);
const isLastStep = computed(() => props.currentIndex >= props.steps.length - 1);

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function updateLayout(): void {
  if (!props.open || !currentStep.value) {
    spotlightRect.value = null;
    cardStyle.value = {};
    retryCount = 0;
    if (retryTimer) {
      clearTimeout(retryTimer);
      retryTimer = null;
    }
    return;
  }

  const target = document.querySelector(currentStep.value.target);
  if (!(target instanceof HTMLElement)) {
    spotlightRect.value = null;
    cardStyle.value = {
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -50%)"
    };
    if (retryCount < 8) {
      retryCount += 1;
      if (retryTimer) {
        clearTimeout(retryTimer);
      }
      retryTimer = setTimeout(() => {
        updateLayout();
      }, 120);
    }
    return;
  }
  retryCount = 0;
  if (retryTimer) {
    clearTimeout(retryTimer);
    retryTimer = null;
  }

  target.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
  const rect = target.getBoundingClientRect();
  spotlightRect.value = rect;

  const hasRichContent = Boolean(
    currentStep.value.image || (currentStep.value.bullets?.length ?? 0) > 0
  );
  const cardWidth = Math.min(hasRichContent ? 360 : 320, window.innerWidth - 32);
  const cardHeight = tourCardRef.value?.offsetHeight ?? 196;
  const gap = 16;
  const placement = currentStep.value.placement ?? "bottom";
  let top = rect.bottom + gap;
  let left = rect.left + rect.width / 2 - cardWidth / 2;

  if (placement === "top") {
    top = rect.top - cardHeight - gap;
  } else if (placement === "left") {
    top = rect.top + rect.height / 2 - cardHeight / 2;
    left = rect.left - cardWidth - gap;
  } else if (placement === "right") {
    top = rect.top + rect.height / 2 - cardHeight / 2;
    left = rect.right + gap;
  }

  top = clamp(top, 16, window.innerHeight - cardHeight - 16);
  left = clamp(left, 16, window.innerWidth - cardWidth - 16);

  cardStyle.value = {
    width: `${cardWidth}px`,
    top: `${top}px`,
    left: `${left}px`
  };
}

async function refreshLayout(): Promise<void> {
  await nextTick();
  window.requestAnimationFrame(updateLayout);
}

watch(
  () => [props.open, props.currentIndex, props.steps.length],
  () => {
    void refreshLayout();
  },
  { immediate: true }
);

onMounted(() => {
  window.addEventListener("resize", updateLayout);
  window.addEventListener("scroll", updateLayout, true);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", updateLayout);
  window.removeEventListener("scroll", updateLayout, true);
  if (retryTimer) {
    clearTimeout(retryTimer);
  }
});
</script>

<template>
  <teleport to="body">
    <div v-if="open && currentStep" class="tour-layer" aria-live="polite">
      <div class="tour-backdrop" @click="emit('close')"></div>
      <div v-if="spotlightRect" class="tour-spotlight" :style="{
        top: `${spotlightRect.top - 8}px`,
        left: `${spotlightRect.left - 8}px`,
        width: `${spotlightRect.width + 16}px`,
        height: `${spotlightRect.height + 16}px`
      }"></div>
      <aside ref="tourCardRef" class="tour-card" :style="cardStyle">
        <div class="tour-context">
          <span v-if="flowSectionLabel" class="tour-flow-label">{{ flowSectionLabel }}</span>
          <span class="tour-step-count">{{ flowLabel || "新手教學" }} · 步驟 {{ currentIndex + 1 }} / {{ steps.length }}</span>
        </div>
        <h3>{{ currentStep.title }}</h3>

        <img
          v-if="currentStep.image"
          class="tour-image"
          :src="currentStep.image.src"
          :alt="currentStep.image.alt"
          @load="refreshLayout"
        />

        <p>{{ currentStep.description }}</p>

        <ul v-if="currentStep.bullets?.length" class="tour-bullets">
          <li v-for="(bullet, i) in currentStep.bullets" :key="i">{{ bullet }}</li>
        </ul>

        <div v-if="currentStep.example?.length" class="tour-examples">
          <div v-for="(ex, i) in currentStep.example" :key="i" class="tour-example-row">
            <span v-if="ex.label" class="tour-example-label">{{ ex.label }}</span>
            <code class="tour-example-value">{{ ex.value }}</code>
          </div>
        </div>

        <div
          v-if="currentStep.note"
          class="tour-note"
          :class="`tour-note-${currentStep.note.tone}`"
        >
          <span class="tour-note-icon" aria-hidden="true">{{ currentStep.note.tone === "warning" ? "⚠" : "ℹ" }}</span>
          <span>{{ currentStep.note.text }}</span>
        </div>
      </aside>
      <div class="tour-floating-actions">
        <button class="outline-btn" type="button" @click="emit('close')">結束</button>
        <button class="outline-btn" type="button" :disabled="isFirstStep" @click="emit('prev')">上一步</button>
        <button class="primary-btn" type="button" @click="isLastStep ? emit('close') : emit('next')">
          {{ isLastStep ? "完成" : "下一步" }}
        </button>
      </div>
    </div>
  </teleport>
</template>

<style scoped>
.tour-layer {
  position: fixed;
  inset: 0;
  z-index: 120;
}

.tour-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.34);
}

.tour-spotlight {
  position: fixed;
  border-radius: 14px;
  border: 2px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 0 0 9999px rgba(15, 23, 42, 0.16), 0 18px 40px rgba(15, 23, 42, 0.18);
  pointer-events: none;
}

.tour-card {
  position: fixed;
  display: grid;
  gap: 10px;
  padding: 16px;
  border: 1px solid rgba(214, 224, 238, 0.96);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.24);
}

.tour-context {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.tour-flow-label {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(47, 110, 229, 0.12);
  color: #1f5fcf;
  font-size: 10px;
  font-weight: 800;
}

.tour-step-count {
  color: #2f6ee5;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.tour-card h3 {
  margin: 0;
  color: #20304f;
  font-size: 18px;
}

.tour-card p {
  margin: 0;
  color: #55657f;
  font-size: 13px;
  line-height: 1.6;
}

.tour-image {
  display: block;
  width: 100%;
  max-height: 160px;
  object-fit: contain;
  border-radius: 10px;
  border: 1px solid rgba(214, 224, 238, 0.96);
  background: #f4f7fb;
}

.tour-bullets {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
  color: #45536b;
  font-size: 13px;
  line-height: 1.55;
}

.tour-bullets li::marker {
  color: #2f6ee5;
}

.tour-examples {
  display: grid;
  gap: 6px;
}

.tour-example-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
  padding: 6px 10px;
  border-radius: 8px;
  background: #f4f7fb;
  border: 1px solid rgba(214, 224, 238, 0.96);
}

.tour-example-label {
  color: #5b6b84;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.tour-example-value {
  color: #20304f;
  font-size: 12px;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  word-break: break-all;
  white-space: pre-wrap;
}

.tour-note {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 12px;
  line-height: 1.6;
}

.tour-note-warning {
  color: #8a4b0a;
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.32);
}

.tour-note-info {
  color: #1f4d8f;
  background: rgba(47, 110, 229, 0.1);
  border: 1px solid rgba(47, 110, 229, 0.28);
}

.tour-note-icon {
  flex: none;
  font-size: 13px;
  line-height: 1.6;
}

.tour-floating-actions {
  position: fixed;
  right: 20px;
  bottom: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
  z-index: 121;
  pointer-events: auto;
  padding: 10px 12px;
  border: 1px solid rgba(214, 224, 238, 0.96);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.18);
}

.tour-floating-actions button {
  width: auto;
}

@media (max-width: 720px) {
  .tour-card {
    width: calc(100vw - 24px) !important;
    left: 12px !important;
    right: 12px;
    top: auto !important;
    bottom: 12px;
  }

  .tour-floating-actions {
    right: 12px;
    bottom: 12px;
    left: 12px;
    justify-content: flex-end;
  }
}
</style>
