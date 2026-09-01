<script setup lang="ts">
defineProps<{
  fields: Array<{ label: string; value: string }>;
  entityLabel: string;
  onEdit: () => void;
}>();
</script>

<template>
  <section class="readonly-summary" aria-live="polite">
    <div v-if="fields.length === 0" class="readonly-empty">
      <span class="empty-icon" aria-hidden="true">⌁</span>
      <strong>尚未選擇資料</strong>
      <p>請從左側清單選擇一筆{{ entityLabel }}，即可先查看摘要；需要修改時再按「編輯」。</p>
    </div>
    <template v-else>
      <dl class="summary-grid">
        <div v-for="field in fields" :key="field.label" class="summary-field">
          <dt>{{ field.label }}</dt>
          <dd>{{ field.value }}</dd>
        </div>
      </dl>
      <div class="summary-actions">
        <button class="primary-btn" type="button" @click="onEdit">編輯這筆資料</button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.readonly-summary {
  display: grid;
  align-content: start;
  gap: 14px;
  min-height: 220px;
  padding: 8px 2px 2px;
}

.readonly-empty {
  display: grid;
  justify-items: center;
  gap: 8px;
  margin: auto;
  max-width: 420px;
  padding: 40px 24px;
  color: #61708a;
  text-align: center;
}

.readonly-empty strong {
  color: #263957;
  font-size: 15px;
}

.readonly-empty p {
  margin: 0;
  font-size: 12px;
  line-height: 1.7;
}

.empty-icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border: 1px solid #d7e2f2;
  border-radius: 50%;
  color: #5577ad;
  background: #f3f7fd;
  font-size: 24px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
}

.summary-field {
  display: grid;
  gap: 5px;
  min-width: 0;
  padding: 11px 12px;
  border: 1px solid #dde6f2;
  border-radius: 9px;
  background: #fbfdff;
}

.summary-field dt {
  color: #687892;
  font-size: 11px;
  font-weight: 700;
}

.summary-field dd {
  margin: 0;
  color: #223653;
  font-size: 13px;
  font-weight: 650;
  overflow-wrap: anywhere;
}

.summary-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 4px;
}

.primary-btn {
  min-height: 34px;
  border: 1px solid #356bc2;
  border-radius: 9px;
  padding: 7px 14px;
  color: #fff;
  background: linear-gradient(180deg, #4f83d5 0%, #356bc2 100%);
  font: inherit;
  font-size: 12px;
  font-weight: 750;
  cursor: pointer;
}

.primary-btn:hover {
  filter: brightness(1.04);
}

@media (max-width: 700px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
