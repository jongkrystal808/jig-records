<script setup lang="ts">
import BatchImportPanel from "@/components/inventory/BatchImportPanel.vue";

type ImportMode = "receipt" | "return";

withDefaults(defineProps<{
  customerId: number | undefined;
  initialMode?: ImportMode;
  presetFixtureCode?: string;
}>(), {
  initialMode: "receipt",
  presetFixtureCode: ""
});

const emit = defineEmits<{ success: [] }>();
</script>

<template>
  <div class="workbench-batch-workspace" data-workbench-component="batch-operations">
    <header class="workbench-batch-intro">
      <div>
        <span class="workbench-batch-kicker">BATCH DESK</span>
        <h3>批次收退料工作區</h3>
        <p>每一列可獨立選擇收料或退料；掃描、直接輸入或從 Excel 貼上都在同一張工作表完成。</p>
      </div>
      <ol aria-label="批次收退料流程">
        <li><b>1</b><span>輸入或貼上</span></li>
        <li><b>2</b><span>檢查例外</span></li>
        <li><b>3</b><span>確認送出</span></li>
      </ol>
    </header>

    <BatchImportPanel
      class="workbench-batch-core"
      :customer-id="customerId"
      :initial-mode="initialMode"
      :show-mode-switch="true"
      :preset-fixture-code="presetFixtureCode"
      :hide-frame="true"
      title="批次收退料"
      description="工作台批次作業"
      @success="emit('success')"
    />
  </div>
</template>

<style scoped>
.workbench-batch-workspace {
  display: grid;
  min-width: 0;
  gap: 12px;
}

.workbench-batch-intro {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 18px;
  padding: 14px 16px;
  border: 1px solid var(--workbench-border, var(--line));
  border-radius: 16px;
  background:
    radial-gradient(circle at 92% 15%, rgba(255, 255, 255, 0.86), transparent 32%),
    linear-gradient(135deg, #f8fbff 0%, var(--workbench-blue-soft, #edf4ff) 100%);
}

.workbench-batch-kicker {
  display: inline-flex;
  margin-bottom: 4px;
  color: var(--workbench-blue-strong, #245fc9);
  font-size: 0.62rem;
  font-weight: 900;
  letter-spacing: 0.13em;
}

.workbench-batch-intro h3,
.workbench-batch-intro p {
  margin: 0;
}

.workbench-batch-intro h3 { font-size: 1rem; }
.workbench-batch-intro p { margin-top: 4px; color: var(--muted); font-size: 0.72rem; }

.workbench-batch-intro ol {
  display: flex;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.workbench-batch-intro li {
  display: grid;
  min-width: 82px;
  gap: 3px;
  padding: 8px 10px;
  border: 1px solid color-mix(in srgb, var(--tone-info) 18%, var(--line));
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.78);
}

.workbench-batch-intro li b { color: var(--tone-info); font-size: 0.68rem; }
.workbench-batch-intro li span { color: #52617a; font-size: 0.66rem; font-weight: 800; }

@media (max-width: 1080px) {
  .workbench-batch-intro { grid-template-columns: 1fr; }
  .workbench-batch-intro ol { overflow-x: auto; }
}
</style>
