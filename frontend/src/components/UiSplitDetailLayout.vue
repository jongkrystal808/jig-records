<script setup lang="ts">
// Keep the repeated summary-rail/detail-scroll shell centralized so detail panels only describe their content blocks.
</script>

<template>
  <div class="ui-split-detail-layout">
    <aside class="ui-split-detail-rail">
      <slot name="summary" />
    </aside>
    <div class="ui-detail-scroll">
      <slot />
    </div>
  </div>
</template>
