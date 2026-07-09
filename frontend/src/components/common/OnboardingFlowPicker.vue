<script setup lang="ts">
import type { OnboardingFlowId } from "@/onboarding";

type OnboardingFlowCard = {
  id: OnboardingFlowId;
  sectionLabel: string;
  label: string;
  summary: string;
  stepCount: number;
  disabled: boolean;
  disabledReason: string;
};

defineProps<{
  open: boolean;
  flows: OnboardingFlowCard[];
}>();

const emit = defineEmits<{
  close: [];
  select: [flowId: OnboardingFlowId];
}>();
</script>

<template>
  <teleport to="body">
    <div v-if="open" class="picker-layer" aria-live="polite">
      <div class="picker-backdrop" @click="emit('close')"></div>
      <section class="picker-card">
        <header class="picker-head">
          <div>
            <span class="picker-eyebrow">Onboarding</span>
            <h2>選擇要看的教學</h2>
            <p>教學已依頁面與分頁拆開。直接挑你現在要學的功能，不用一次看完整套流程。</p>
          </div>
          <button class="outline-btn" type="button" @click="emit('close')">關閉</button>
        </header>

        <div class="picker-grid">
          <article
            v-for="flow in flows"
            :key="flow.id"
            class="flow-card"
            :class="{ disabled: flow.disabled }"
          >
            <div class="flow-meta">
              <span class="flow-section">{{ flow.sectionLabel }}</span>
              <span class="flow-steps">{{ flow.stepCount }} 步</span>
            </div>
            <h3>{{ flow.label }}</h3>
            <p>{{ flow.summary }}</p>
            <button
              class="primary-btn flow-start-btn"
              type="button"
              :disabled="flow.disabled"
              @click="emit('select', flow.id)"
            >
              {{ flow.disabled ? flow.disabledReason : "開始教學" }}
            </button>
          </article>
        </div>
      </section>
    </div>
  </teleport>
</template>

<style scoped>
.picker-layer {
  position: fixed;
  inset: 0;
  z-index: 130;
  display: grid;
  place-items: center;
  padding: 12px;
}

.picker-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
}

.picker-card {
  position: relative;
  z-index: 1;
  width: min(980px, 100%);
  max-height: 100%;
  overflow: auto;
  border: 1px solid rgba(214, 224, 238, 0.96);
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(46, 109, 229, 0.12), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 251, 255, 0.98) 100%);
  box-shadow: 0 28px 80px rgba(15, 23, 42, 0.28);
  padding: 22px;
}

.picker-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
}

.picker-eyebrow {
  color: #2f6ee5;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.picker-head h2 {
  margin: 6px 0 0;
  color: #20304f;
  font-size: 28px;
}

.picker-head p {
  margin: 8px 0 0;
  color: #5b6b84;
  font-size: 14px;
  line-height: 1.6;
  max-width: 680px;
}

.picker-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.flow-card {
  display: grid;
  gap: 10px;
  padding: 18px;
  border: 1px solid rgba(210, 220, 234, 0.96);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
}

.flow-card.disabled {
  opacity: 0.72;
}

.flow-meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.flow-section,
.flow-steps {
  color: #5b6b84;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.flow-card h3 {
  margin: 0;
  color: #22314a;
  font-size: 18px;
}

.flow-card p {
  margin: 0;
  color: #5d6d89;
  font-size: 13px;
  line-height: 1.65;
  min-height: 64px;
}

.flow-start-btn {
  width: auto;
  justify-self: start;
}

@media (max-width: 900px) {
  .picker-layer {
    padding: 10px;
  }

  .picker-card {
    padding: 16px;
  }

  .picker-grid {
    grid-template-columns: 1fr;
  }

  .picker-head {
    flex-direction: column;
  }
}
</style>
