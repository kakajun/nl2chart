<template>
  <div class="app-layout">
    <aside class="nav-sidebar" :class="{ collapsed: navCollapsed }">
      <div class="nav-header">
        <div class="logo">
          <span class="logo-icon">⚡</span>
          <span v-if="!navCollapsed" class="logo-text">SCADA</span>
        </div>
        <button class="nav-toggle" @click="navCollapsed = !navCollapsed">
          {{ navCollapsed ? '›' : '‹' }}
        </button>
      </div>
      <nav class="nav-menu">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span v-if="!navCollapsed" class="nav-label">{{ item.title }}</span>
        </router-link>
      </nav>
      <div class="nav-footer">
        <span v-if="!navCollapsed" class="nav-version">v1.0.0</span>
      </div>
    </aside>

    <main class="main-content">
      <div class="content-wrapper">
        <router-view />
      </div>
    </main>

    <aside class="right-panel">
      <div class="panel-section">
        <h4>实时状态</h4>
        <div class="status-grid">
          <div class="status-cell">
            <span class="status-label">数据源</span>
            <span class="status-badge" :class="dataSource">{{ dataSourceText }}</span>
          </div>
          <div class="status-cell">
            <span class="status-label">数据量</span>
            <span class="status-value">{{ dataCount }}</span>
          </div>
          <div class="status-cell">
            <span class="status-label">最后更新</span>
            <span class="status-value">{{ lastUpdate }}</span>
          </div>
        </div>
      </div>
      <div class="panel-section">
        <h4>快速告警</h4>
        <div v-if="latestAlerts.length === 0" class="panel-empty">无告警</div>
        <div
          v-for="alert in latestAlerts.slice(0, 5)"
          :key="alert.id"
          class="alert-mini"
          :class="alert.level"
        >
          <span class="alert-dot" />
          <span class="alert-msg">{{ alert.alert_type }}</span>
        </div>
      </div>
      <div class="panel-section">
        <h4>在线设备</h4>
        <div class="device-mini-list">
          <div v-for="dev in onlineDevices" :key="dev" class="device-mini">
            <span class="device-dot online" />
            <span>{{ dev }}</span>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";

const API_BASE = import.meta.env.VITE_API_BASE || "";

const navCollapsed = ref(false);
const navItems = [
  { path: "/monitor", title: "SCADA监控", icon: "📊" },
  { path: "/query", title: "数据查询", icon: "🔍" },
  { path: "/alerts", title: "告警中心", icon: "🚨" },
  { path: "/devices", title: "设备管理", icon: "⚙️" },
  { path: "/settings", title: "系统设置", icon: "🔧" },
];

const dataSource = ref("mock");
const dataSourceText = ref("模拟数据");
const dataCount = ref("--");
const lastUpdate = ref("--");
const latestAlerts = ref([]);
const onlineDevices = ref([]);

let statusTimer = null;

async function loadStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/scada/status`);
    const data = await res.json();
    dataSource.value = data.data_source;
    dataSourceText.value = data.message;
    lastUpdate.value = new Date().toLocaleTimeString("zh-CN", { hour12: false });
  } catch {}
}

async function loadAlerts() {
  try {
    const res = await fetch(`${API_BASE}/api/scada/alerts?station_code=HBZ&limit=10`);
    const data = await res.json();
    latestAlerts.value = data.alerts || [];
  } catch {}
}

async function loadMetrics() {
  try {
    const res = await fetch(`${API_BASE}/api/scada/metrics/HBZ`);
    const data = await res.json();
    const pts = data.latest_points || [];
    dataCount.value = pts.length.toString();
    const devs = new Set();
    for (const p of pts) {
      if (p.equ_code) devs.add(p.equ_code);
    }
    onlineDevices.value = Array.from(devs).slice(0, 8);
  } catch {}
}

onMounted(() => {
  loadStatus();
  loadAlerts();
  loadMetrics();
  statusTimer = setInterval(() => {
    loadStatus();
    loadAlerts();
    loadMetrics();
  }, 30000);
});

onUnmounted(() => {
  if (statusTimer) clearInterval(statusTimer);
});
</script>

<style>
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: #0a0e1a;
  color: #e0e6ed;
  overflow: hidden;
}
</style>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* 左侧导航栏 */
.nav-sidebar {
  width: 200px;
  flex-shrink: 0;
  background: #111827;
  border-right: 1px solid #1e293b;
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease;
}
.nav-sidebar.collapsed {
  width: 56px;
}
.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 12px;
  border-bottom: 1px solid #1e293b;
}
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}
.logo-icon {
  font-size: 20px;
  flex-shrink: 0;
}
.logo-text {
  font-size: 16px;
  font-weight: 600;
  color: #e0e6ed;
  white-space: nowrap;
}
.nav-toggle {
  width: 24px;
  height: 24px;
  border: 1px solid #374151;
  background: transparent;
  color: #94a3b8;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}
.nav-toggle:hover {
  border-color: #4dabf7;
  color: #4dabf7;
}
.nav-menu {
  flex: 1;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  color: #94a3b8;
  text-decoration: none;
  font-size: 13px;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
  overflow: hidden;
}
.nav-item:hover {
  background: #1e293b;
  color: #e0e6ed;
}
.nav-item.active {
  background: #4dabf722;
  color: #4dabf7;
}
.nav-icon {
  font-size: 16px;
  flex-shrink: 0;
}
.nav-label {
  font-size: 13px;
}
.nav-footer {
  padding: 12px;
  border-top: 1px solid #1e293b;
  text-align: center;
}
.nav-version {
  font-size: 11px;
  color: #64748b;
}

/* 中间内容区 */
.main-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.content-wrapper {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  min-height: 0;
}

/* 右侧辅助面板 */
.right-panel {
  width: 220px;
  flex-shrink: 0;
  background: #111827;
  border-left: 1px solid #1e293b;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}
.panel-section h4 {
  margin: 0 0 10px 0;
  font-size: 12px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.status-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.status-cell {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}
.status-label {
  color: #64748b;
}
.status-value {
  color: #e0e6ed;
  font-family: monospace;
}
.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}
.status-badge.tdengine {
  background: #00d26a33;
  color: #00d26a;
}
.status-badge.mock {
  background: #f59e0b33;
  color: #f59e0b;
}
.panel-empty {
  font-size: 12px;
  color: #64748b;
  padding: 8px 0;
}
.alert-mini {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  font-size: 12px;
  border-bottom: 1px solid #1e293b;
}
.alert-mini:last-child {
  border-bottom: none;
}
.alert-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.alert-mini.urgent .alert-dot { background: #ef4444; }
.alert-mini.warning .alert-dot { background: #f59e0b; }
.alert-mini.info .alert-dot { background: #3b82f6; }
.alert-msg {
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.device-mini-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.device-mini {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #94a3b8;
}
.device-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.device-dot.online { background: #00d26a; }

/* 响应式 */
@media (max-width: 1200px) {
  .right-panel {
    display: none;
  }
}
@media (max-width: 768px) {
  .nav-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    transform: translateX(-100%);
  }
  .nav-sidebar.collapsed {
    transform: translateX(-100%);
  }
  .nav-sidebar:not(.collapsed) {
    transform: translateX(0);
  }
}
</style>
