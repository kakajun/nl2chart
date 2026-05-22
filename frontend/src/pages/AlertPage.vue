<template>
  <div class="alert-page">
    <header class="page-header">
      <h1>告警中心</h1>
      <div class="alert-stats">
        <span class="stat urgent">紧急 {{ urgentCount }}</span>
        <span class="stat warn">警告 {{ warnCount }}</span>
        <span class="stat info">提示 {{ infoCount }}</span>
      </div>
    </header>
    <div class="alert-toolbar">
      <button class="btn-refresh" @click="loadAlerts">刷新</button>
      <select v-model="filterLevel" class="filter-select">
        <option value="">全部等级</option>
        <option value="urgent">紧急</option>
        <option value="warning">警告</option>
        <option value="info">提示</option>
      </select>
      <select v-model="filterResolved" class="filter-select">
        <option value="">全部状态</option>
        <option value="false">未处理</option>
        <option value="true">已处理</option>
      </select>
    </div>
    <div class="alert-list">
      <div v-if="filteredAlerts.length === 0" class="empty">暂无告警</div>
      <div
        v-for="alert in filteredAlerts"
        :key="alert.id"
        class="alert-item"
        :class="alert.level"
      >
        <div class="alert-icon" :class="alert.level">
          {{ alert.level === 'urgent' ? '🔴' : alert.level === 'warning' ? '🟡' : '🔵' }}
        </div>
        <div class="alert-body">
          <div class="alert-title">{{ alert.alert_type }}</div>
          <div class="alert-msg">{{ alert.message }}</div>
          <div class="alert-meta">
            <span>{{ alert.station_code }} / {{ alert.equ_code }}</span>
            <span>{{ alert.ts }}</span>
          </div>
        </div>
        <div class="alert-action">
          <button v-if="!alert.resolved" class="btn-resolve" @click="resolveAlert(alert.id)">
            确认处理
          </button>
          <span v-else class="resolved-tag">已处理</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";

const API_BASE = import.meta.env.VITE_API_BASE || "";

const alerts = ref([]);
const filterLevel = ref("");
const filterResolved = ref("");

const filteredAlerts = computed(() => {
  let list = alerts.value;
  if (filterLevel.value) {
    list = list.filter((a) => a.level === filterLevel.value);
  }
  if (filterResolved.value !== "") {
    list = list.filter((a) => String(a.resolved) === filterResolved.value);
  }
  return list;
});

const urgentCount = computed(() => alerts.value.filter((a) => a.level === "urgent" && !a.resolved).length);
const warnCount = computed(() => alerts.value.filter((a) => a.level === "warning" && !a.resolved).length);
const infoCount = computed(() => alerts.value.filter((a) => a.level === "info" && !a.resolved).length);

async function loadAlerts() {
  try {
    const res = await fetch(`${API_BASE}/api/scada/alerts?station_code=HBZ&limit=200`);
    const data = await res.json();
    alerts.value = data.alerts || [];
  } catch (e) {
    console.error("加载告警失败", e);
  }
}

async function resolveAlert(id) {
  // TODO: call PATCH API
  const alert = alerts.value.find((a) => a.id === id);
  if (alert) alert.resolved = true;
}

onMounted(() => {
  loadAlerts();
});
</script>

<style scoped>
.alert-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-header h1 {
  margin: 0;
  font-size: 18px;
}
.alert-stats {
  display: flex;
  gap: 12px;
}
.stat {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
.stat.urgent {
  background: #ef444433;
  color: #ef4444;
}
.stat.warn {
  background: #f59e0b33;
  color: #f59e0b;
}
.stat.info {
  background: #3b82f633;
  color: #3b82f6;
}
.alert-toolbar {
  display: flex;
  gap: 8px;
}
.btn-refresh {
  padding: 6px 14px;
  border: 1px solid #374151;
  background: transparent;
  color: #94a3b8;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.filter-select {
  padding: 6px 10px;
  border: 1px solid #374151;
  background: #0a0e1a;
  color: #e0e6ed;
  border-radius: 4px;
  font-size: 12px;
}
.alert-list {
  flex: 1;
  background: #111827;
  border-radius: 8px;
  padding: 12px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.empty {
  text-align: center;
  padding: 40px;
  color: #64748b;
}
.alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #0a0e1a;
  border-radius: 8px;
  border-left: 3px solid transparent;
}
.alert-item.urgent {
  border-left-color: #ef4444;
}
.alert-item.warning {
  border-left-color: #f59e0b;
}
.alert-item.info {
  border-left-color: #3b82f6;
}
.alert-icon {
  font-size: 20px;
}
.alert-body {
  flex: 1;
  min-width: 0;
}
.alert-title {
  font-size: 14px;
  font-weight: 500;
  color: #e0e6ed;
}
.alert-msg {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}
.alert-meta {
  font-size: 11px;
  color: #64748b;
  margin-top: 4px;
  display: flex;
  gap: 12px;
}
.alert-action {
  flex-shrink: 0;
}
.btn-resolve {
  padding: 6px 12px;
  border: none;
  background: #4dabf7;
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.resolved-tag {
  padding: 4px 10px;
  background: #1e293b;
  border-radius: 4px;
  font-size: 12px;
  color: #64748b;
}
</style>
