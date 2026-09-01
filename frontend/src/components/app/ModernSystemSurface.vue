<script setup lang="ts">
import { RouterView } from "vue-router";
</script>

<template>
  <section class="modern-system-surface" data-system-ui="modern" aria-label="Modern UI 系統介面">
    <RouterView />
  </section>
</template>

<style scoped>
.modern-system-surface {
  min-height: 100%;
}
</style>
