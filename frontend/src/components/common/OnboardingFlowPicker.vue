<script setup lang="ts">
import { computed } from "vue";

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

const props = defineProps<{
  open: boolean;
  flows: OnboardingFlowCard[];
}>();

const emit = defineEmits<{
  close: [];
  select: [flowId: OnboardingFlowId];
}>();

const detailedFlow = computed(() => props.flows.find((flow) => flow.id === "system-detailed-guide") ?? null);
const conciseFlows = computed(() => props.flows.filter((flow) => flow.id !== "system-detailed-guide"));
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
            <p>可選單一功能的精簡教學，也可選「全系統按鈕與操作說明」詳細版，從首頁一路認識各工作頁。</p>
          </div>
          <button class="outline-btn" type="button" @click="emit('close')">關閉</button>
        </header>

        <section v-if="detailedFlow" class="picker-section detailed-section" aria-labelledby="detailed-guide-heading">
          <div class="section-head">
            <div>
              <span class="section-kicker">推薦入口</span>
              <h3 id="detailed-guide-heading">完整詳細版</h3>
            </div>
            <span class="section-hint">第一次完整認識系統，請從這裡開始</span>
          </div>
          <article class="flow-card detailed-flow-card" :class="{ disabled: detailedFlow.disabled }">
            <div class="detailed-copy">
              <div class="flow-meta">
                <span class="flow-section">{{ detailedFlow.sectionLabel }}</span>
                <span class="flow-steps">{{ detailedFlow.stepCount }} 步</span>
              </div>
              <h3>{{ detailedFlow.label }}</h3>
              <p>{{ detailedFlow.summary }}</p>
            </div>
            <button
              class="primary-btn flow-start-btn detailed-start-btn"
              type="button"
              :disabled="detailedFlow.disabled"
              @click="emit('select', detailedFlow.id)"
            >
              {{ detailedFlow.disabled ? detailedFlow.disabledReason : "開始完整詳細版" }}
            </button>
          </article>
        </section>

        <section class="picker-section" aria-labelledby="concise-guide-heading">
          <div class="section-head">
            <div>
              <span class="section-kicker">快速查閱</span>
              <h3 id="concise-guide-heading">功能精簡教學</h3>
            </div>
            <span class="section-hint">只想了解單一功能時再選下方卡片</span>
          </div>
          <div class="picker-grid">
          <article
            v-for="flow in conciseFlows"
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

.picker-section {
  display: grid;
  gap: 12px;
}

.picker-section + .picker-section {
  margin-top: 22px;
  padding-top: 20px;
  border-top: 1px solid rgba(210, 220, 234, 0.9);
}

.section-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 14px;
}

.section-head h3 {
  margin: 3px 0 0;
  color: #20304f;
  font-size: 20px;
}

.section-kicker {
  color: #2f6ee5;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.section-hint {
  color: #64748b;
  font-size: 12px;
}

.picker-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.detailed-flow-card {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  border-color: rgba(47, 110, 229, 0.38);
  background:
    radial-gradient(circle at top right, rgba(47, 110, 229, 0.18), transparent 35%),
    linear-gradient(135deg, rgba(239, 246, 255, 0.98) 0%, rgba(255, 255, 255, 0.98) 72%);
  box-shadow: 0 16px 36px rgba(47, 110, 229, 0.12);
}

.detailed-copy {
  display: grid;
  gap: 10px;
}

.detailed-flow-card p {
  min-height: 0;
}

.detailed-start-btn {
  min-width: 168px;
  justify-self: end;
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

  .section-head,
  .detailed-flow-card {
    align-items: flex-start;
    grid-template-columns: 1fr;
  }

  .section-head {
    flex-direction: column;
    gap: 4px;
  }

  .detailed-start-btn {
    width: 100%;
    justify-self: stretch;
  }
}
</style>
