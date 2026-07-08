<script setup lang="ts">
const props = defineProps<{
  username: string;
  password: string;
  loggingIn: boolean;
}>();

const emit = defineEmits<{
  "update:username": [value: string];
  "update:password": [value: string];
  login: [];
  guestEntry: [];
}>();

// Keep unauthenticated UI isolated so App.vue only owns session flow and auth side effects.
</script>

<template>
  <section class="login-shell">
    <article class="login-card">
      <header class="login-brand">
        <div class="login-brand-mark" aria-hidden="true">JR</div>
        <div>
          <p class="login-eyebrow">Jig Record</p>
          <h1>人員登入入口</h1>
        </div>
      </header>
      <p class="login-copy">請使用帳號密碼登入，或以訪客身分進入系統。</p>
      <form class="login-form" @submit.prevent="emit('login')">
        <label>
          <span>帳號</span>
          <input :value="username" name="username" autocomplete="username" spellcheck="false" required @input="emit('update:username', ($event.target as HTMLInputElement).value)" />
        </label>
        <label>
          <span>密碼</span>
          <input :value="password" name="password" autocomplete="current-password" type="password" required @input="emit('update:password', ($event.target as HTMLInputElement).value)" />
        </label>
        <button class="primary-btn" type="submit" :disabled="loggingIn">{{ loggingIn ? "登入中..." : "登入" }}</button>
      </form>
      <button class="outline-btn" type="button" :disabled="loggingIn" @click="emit('guestEntry')">訪客入口</button>
    </article>
  </section>
</template>

<style scoped>
.login-shell {
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 24px;
}

.login-card {
  width: min(460px, 100%);
  padding: 30px;
  border: 1px solid rgba(214, 224, 238, 0.94);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 250, 255, 0.96) 100%);
  box-shadow: 0 28px 60px rgba(28, 47, 84, 0.14);
  display: grid;
  gap: 16px;
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.login-brand-mark {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: linear-gradient(180deg, #183055 0%, #0f213e 100%);
  color: #edf4ff;
  font-weight: 800;
}

.login-eyebrow {
  margin: 0;
  color: #2f6ee5;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.login-card h1 {
  margin: 0;
  color: #1f2b45;
}

.login-copy {
  margin: 0;
  color: #5d6d89;
  font-size: 14px;
}

.login-form {
  display: grid;
  gap: 12px;
}

.login-form label {
  display: grid;
  gap: 6px;
}

.login-form span {
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
}

input {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  color: var(--text);
}

</style>
