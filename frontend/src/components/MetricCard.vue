<template>
  <div class="metric-card">
    <div class="title">{{ title }}</div>
    <div class="value" :style="{ color }">
      {{ value }}
      <span class="unit">{{ unit }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  value: String,
  unit: String,
  color: { type: String, default: "#fff" },
});
</script>

<style scoped>
.metric-card {
  background: #111827;
  border-radius: 8px;
  padding: 20px;
}
.title {
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 8px;
}
.value {
  font-size: 32px;
  font-weight: 600;
  letter-spacing: -1px;
}
.unit {
  font-size: 14px;
  color: #64748b;
  margin-left: 4px;
  font-weight: 400;
}
</style>
