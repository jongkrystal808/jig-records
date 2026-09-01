<script setup lang="ts">
import { ref, watch } from "vue";

import { api } from "@/api";
import UiModalShell from "@/components/common/UiModalShell.vue";
import { pushToast } from "@/toastState";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ close: [] }>();

const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const saving = ref(false);

function reset(): void {
  currentPassword.value = "";
  newPassword.value = "";
  confirmPassword.value = "";
}

function close(): void {
  if (!saving.value) emit("close");
}

async function submit(): Promise<void> {
  if (!currentPassword.value) {
    pushToast("請輸入目前密碼。", "warning");
    return;
  }
  if (newPassword.value.length < 6) {
    pushToast("新密碼至少需要 6 個字元。", "warning");
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    pushToast("兩次輸入的新密碼不一致。", "warning");
    return;
  }
  saving.value = true;
  try {
    await api.changeOwnPassword(currentPassword.value, newPassword.value);
    pushToast("密碼已更新。", "success");
    emit("close");
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "密碼更新失敗", "error");
  } finally {
    saving.value = false;
  }
}

watch(() => props.open, (open) => {
  if (open) reset();
});
</script>

<template>
  <UiModalShell
    :open="open"
    labelled-by="own-password-title"
    described-by="own-password-description"
    dialog-class="own-password-dialog"
    :close-on-backdrop="!saving"
    @close="close"
  >
    <form class="own-password-form" @submit.prevent="submit">
      <header>
        <p>Account Security</p>
        <h2 id="own-password-title">修改自己的密碼</h2>
        <span id="own-password-description">請先輸入目前密碼，再設定至少 6 個字元的新密碼。</span>
      </header>
      <label>
        <span>目前密碼</span>
        <input v-model="currentPassword" type="password" autocomplete="current-password" required data-modal-initial-focus />
      </label>
      <label>
        <span>新密碼</span>
        <input v-model="newPassword" type="password" autocomplete="new-password" minlength="6" required />
      </label>
      <label>
        <span>再次輸入新密碼</span>
        <input v-model="confirmPassword" type="password" autocomplete="new-password" minlength="6" required />
      </label>
      <footer>
        <button class="outline-btn" type="button" :disabled="saving" @click="close">取消</button>
        <button class="primary-btn" type="submit" :disabled="saving">{{ saving ? "更新中…" : "更新密碼" }}</button>
      </footer>
    </form>
  </UiModalShell>
</template>

<style scoped>
.own-password-form { display: grid; gap: 14px; width: min(440px, calc(100vw - 48px)); }
.own-password-form header { display: grid; gap: 5px; }
.own-password-form header p { margin: 0; color: #2f6ee5; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
.own-password-form h2 { margin: 0; color: #1f2b45; }
.own-password-form header span { color: var(--muted); font-size: 0.82rem; }
.own-password-form label { display: grid; gap: 6px; color: #3d4d67; font-size: 0.8rem; font-weight: 700; }
.own-password-form input { min-height: 40px; padding: 8px 10px; border: 1px solid var(--line-strong); border-radius: 8px; font: inherit; }
.own-password-form input:focus { outline: none; border-color: var(--tone-info); box-shadow: 0 0 0 3px var(--tone-info-soft); }
.own-password-form footer { display: flex; justify-content: flex-end; gap: 8px; padding-top: 4px; }
</style>
