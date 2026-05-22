<template>
  <div class="setting-page">
    <header class="page-header">
      <h1>系统设置</h1>
      <p class="desc">SCADA 数据展示系统配置</p>
    </header>
    <div class="settings-body">
      <div class="setting-group">
        <h3>数据源</h3>
        <div class="setting-item">
          <label>当前数据源</label>
          <span class="setting-value" :class="dataSource">{{ dataSourceText }}</span>
        </div>
        <div class="setting-item">
          <label>TDengine 地址</label>
          <input type="text" v-model="tdHost" placeholder="10.204.252.13:6041" />
        </div>
        <div class="setting-item">
          <label>数据库</label>
          <input type="text" v-model="tdDb" placeholder="station_data" />
        </div>
      </div>
      <div class="setting-group">
        <h3>刷新设置</h3>
        <div class="setting-item">
          <label>实时数据刷新间隔（秒）</label>
          <input type="number" v-model="refreshInterval" min="5" max="300" />
        </div>
        <div class="setting-item">
          <label>默认时间范围</label>
          <select v-model="defaultRange">
            <option value="1h">1小时</option>
            <option value="6h">6小时</option>
            <option value="24h">24小时</option>
            <option value="3d">3天</option>
            <option value="7d">7天</option>
          </select>
        </div>
      </div>
      <div class="setting-group">
        <h3>电站信息</h3>
        <div class="setting-item">
          <label>电站编码</label>
          <input type="text" v-model="stationCode" placeholder="HBZ" />
        </div>
        <div class="setting-item">
          <label>电站名称</label>
          <input type="text" v-model="stationName" placeholder="河北张北光伏电站" />
        </div>
      </div>
      <div class="setting-actions">
        <button class="btn-save" @click="saveSettings">保存设置</button>
        <button class="btn-reset" @click="resetSettings">重置</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

const API_BASE = import.meta.env.VITE_API_BASE || "";

const dataSource = ref("mock");
const dataSourceText = ref("模拟数据");
const tdHost = ref("10.204.252.13:6041");
const tdDb = ref("station_data");
const refreshInterval = ref(10);
const defaultRange = ref("24h");
const stationCode = ref("HBZ");
const stationName = ref("河北张北光伏电站");

async function loadStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/scada/status`);
    const data = await res.json();
    dataSource.value = data.data_source;
    dataSourceText.value = data.message;
  } catch {}
}

function saveSettings() {
  localStorage.setItem("scada_settings", JSON.stringify({
    tdHost: tdHost.value,
    tdDb: tdDb.value,
    refreshInterval: refreshInterval.value,
    defaultRange: defaultRange.value,
    stationCode: stationCode.value,
    stationName: stationName.value,
  }));
  alert("设置已保存（仅本地存储）");
}

function resetSettings() {
  tdHost.value = "10.204.252.13:6041";
  tdDb.value = "station_data";
  refreshInterval.value = 10;
  defaultRange.value = "24h";
  stationCode.value = "HBZ";
  stationName.value = "河北张北光伏电站";
}

onMounted(() => {
  loadStatus();
  const saved = localStorage.getItem("scada_settings");
  if (saved) {
    try {
      const s = JSON.parse(saved);
      tdHost.value = s.tdHost || tdHost.value;
      tdDb.value = s.tdDb || tdDb.value;
      refreshInterval.value = s.refreshInterval || refreshInterval.value;
      defaultRange.value = s.defaultRange || defaultRange.value;
      stationCode.value = s.stationCode || stationCode.value;
      stationName.value = s.stationName || stationName.value;
    } catch {}
  }
});
</script>

<style scoped>
.setting-page {
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
.settings-body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.setting-group {
  background: #111827;
  border-radius: 8px;
  padding: 16px;
}
.setting-group h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #94a3b8;
  border-bottom: 1px solid #1e293b;
  padding-bottom: 8px;
}
.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #1e293b;
}
.setting-item:last-child {
  border-bottom: none;
}
.setting-item label {
  font-size: 13px;
  color: #e0e6ed;
}
.setting-item input,
.setting-item select {
  padding: 6px 10px;
  border: 1px solid #374151;
  background: #0a0e1a;
  color: #e0e6ed;
  border-radius: 4px;
  font-size: 13px;
  width: 200px;
}
.setting-value {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
}
.setting-value.tdengine {
  background: #00d26a33;
  color: #00d26a;
}
.setting-value.mock {
  background: #f59e0b33;
  color: #f59e0b;
}
.setting-actions {
  display: flex;
  gap: 12px;
}
.btn-save {
  padding: 8px 20px;
  border: none;
  background: #4dabf7;
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}
.btn-reset {
  padding: 8px 20px;
  border: 1px solid #374151;
  background: transparent;
  color: #94a3b8;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}
</style>
