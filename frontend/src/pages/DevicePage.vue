<template>
  <div class="device-page">
    <header class="page-header">
      <h1>设备管理</h1>
      <p class="desc">电站设备列表与测点映射</p>
    </header>
    <div class="device-list">
      <div v-if="devices.length === 0" class="empty">加载中...</div>
      <div v-for="dev in devices" :key="dev.equ_code" class="device-card">
        <div class="device-header">
          <div class="device-info">
            <span class="device-code">{{ dev.equ_code }}</span>
            <span class="device-model">{{ dev.equ_model }}</span>
            <span class="device-type">{{ dev.equ_type }}</span>
          </div>
          <span class="device-count">{{ dev.points.length }} 测点</span>
        </div>
        <div class="device-points">
          <span v-for="pt in dev.points.slice(0, 20)" :key="pt.code" class="point-tag">
            {{ pt.code }}: {{ pt.name }}
          </span>
          <span v-if="dev.points.length > 20" class="point-tag more">+{{ dev.points.length - 20 }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

const API_BASE = import.meta.env.VITE_API_BASE || "";

const devices = ref([]);

async function loadDevices() {
  try {
    const res = await fetch(`${API_BASE}/api/scada/points/HBZ`);
    const data = await res.json();
    devices.value = data.devices || [];
  } catch (e) {
    console.error("加载设备失败", e);
  }
}

onMounted(() => {
  loadDevices();
});
</script>

<style scoped>
.device-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
}
.page-header h1 {
  margin: 0;
  font-size: 18px;
}
.page-header .desc {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #64748b;
}
.device-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.empty {
  text-align: center;
  padding: 40px;
  color: #64748b;
}
.device-card {
  background: #111827;
  border-radius: 8px;
  padding: 16px;
}
.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.device-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
.device-code {
  font-size: 16px;
  font-weight: 600;
  color: #e0e6ed;
}
.device-model {
  font-size: 12px;
  color: #94a3b8;
  background: #1e293b;
  padding: 2px 8px;
  border-radius: 4px;
}
.device-type {
  font-size: 12px;
  color: #64748b;
}
.device-count {
  font-size: 12px;
  color: #64748b;
}
.device-points {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.point-tag {
  font-size: 11px;
  padding: 3px 8px;
  background: #0a0e1a;
  border-radius: 4px;
  color: #94a3b8;
}
.point-tag.more {
  background: #1e293b;
  color: #4dabf7;
}
</style>
