<template>
  <div class="scada-dashboard">
    <header class="header">
      <h1>新能源 SCADA 监控中心</h1>
      <span class="status" :class="{ online: connected }">
        {{ connected ? "数据在线" : "连接中断" }}
      </span>
    </header>

    <div class="grid">
      <MetricCard
        v-for="m in metrics"
        :key="m.key"
        :title="m.title"
        :value="m.value"
        :unit="m.unit"
        :color="m.color"
      />
    </div>

    <div class="charts-row">
      <div class="chart-panel">
        <h3>发电功率趋势 (24h)</h3>
        <v-chart class="chart" :option="powerOption" autoresize />
      </div>
      <div class="chart-panel">
        <h3>辐照度 / 温度</h3>
        <v-chart class="chart" :option="envOption" autoresize />
      </div>
    </div>

    <div class="alerts-panel">
      <h3>实时告警</h3>
      <table>
        <thead>
          <tr>
            <th>时间</th>
            <th>电站</th>
            <th>类型</th>
            <th>级别</th>
            <th>描述</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="alert in alerts" :key="alert.id" :class="alert.level">
            <td>{{ alert.timestamp }}</td>
            <td>{{ alert.station_id }}</td>
            <td>{{ alert.alert_type }}</td>
            <td>
              <span class="badge" :class="alert.level">{{ alert.level }}</span>
            </td>
            <td>{{ alert.message }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import MetricCard from "./MetricCard.vue";

use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
]);

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const connected = ref(false);
const metrics = ref([
  { key: "power", title: "实时功率", value: "--", unit: "kW", color: "#00d26a" },
  { key: "irradiance", title: "辐照度", value: "--", unit: "W/m²", color: "#ffb800" },
  { key: "temp", title: "板温", value: "--", unit: "°C", color: "#ff6b6b" },
  { key: "wind", title: "风速", value: "--", unit: "m/s", color: "#4dabf7" },
]);

const alerts = ref([]);

const powerOption = ref({
  tooltip: { trigger: "axis" },
  grid: { left: 40, right: 20, top: 20, bottom: 30 },
  xAxis: { type: "category", data: [] },
  yAxis: { type: "value", name: "kW" },
  series: [{ data: [], type: "line", smooth: true, areaStyle: {} }],
});

const envOption = ref({
  tooltip: { trigger: "axis" },
  legend: { data: ["辐照度", "温度"] },
  grid: { left: 40, right: 20, top: 30, bottom: 30 },
  xAxis: { type: "category", data: [] },
  yAxis: [
    { type: "value", name: "W/m²" },
    { type: "value", name: "°C" },
  ],
  series: [
    { name: "辐照度", type: "line", yAxisIndex: 0, data: [] },
    { name: "温度", type: "line", yAxisIndex: 1, data: [] },
  ],
});

async function fetchMetrics(stationId = "station_01") {
  try {
    const res = await fetch(`${API_BASE}/api/scada/metrics/${stationId}`);
    const data = await res.json();
    metrics.value[0].value = data.power_kw?.toFixed(1) ?? "--";
    metrics.value[1].value = data.irradiance?.toFixed(1) ?? "--";
    metrics.value[2].value = data.temperature?.toFixed(1) ?? "--";
    metrics.value[3].value = data.wind_speed?.toFixed(1) ?? "--";
    connected.value = true;
  } catch {
    connected.value = false;
  }
}

async function fetchHistory(stationId = "station_01") {
  try {
    const res = await fetch(
      `${API_BASE}/api/scada/history/${stationId}?metric=power_kw&hours=24&interval=1h`,
    );
    const data = await res.json();
    powerOption.value.xAxis.data = data.labels;
    powerOption.value.series[0].data = data.datasets[0].data;

    const envRes = await fetch(
      `${API_BASE}/api/scada/history/${stationId}?metric=irradiance&hours=24&interval=1h`,
    );
    const envData = await envRes.json();
    envOption.value.xAxis.data = envData.labels;
    envOption.value.series[0].data = envData.datasets[0].data;
  } catch {
    // silent
  }
}

async function fetchAlerts() {
  try {
    const res = await fetch(`${API_BASE}/api/scada/alerts?limit=10`);
    const data = await res.json();
    alerts.value = data.alerts;
  } catch {
    alerts.value = [];
  }
}

onMounted(() => {
  fetchMetrics();
  fetchHistory();
  fetchAlerts();
  setInterval(() => {
    fetchMetrics();
    fetchAlerts();
  }, 10000);
});
</script>

<style scoped>
.scada-dashboard {
  padding: 20px;
  background: #0a0e1a;
  min-height: 100vh;
  color: #e0e6ed;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.header h1 {
  margin: 0;
  font-size: 22px;
}
.status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  background: #333;
}
.status.online {
  background: #00d26a33;
  color: #00d26a;
}
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}
.chart-panel {
  background: #111827;
  border-radius: 8px;
  padding: 16px;
}
.chart-panel h3 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #94a3b8;
}
.chart {
  height: 260px;
}
.alerts-panel {
  background: #111827;
  border-radius: 8px;
  padding: 16px;
}
.alerts-panel h3 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #94a3b8;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th,
td {
  text-align: left;
  padding: 10px;
  border-bottom: 1px solid #1e293b;
}
th {
  color: #64748b;
  font-weight: 500;
}
.badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  text-transform: uppercase;
}
.badge.warning {
  background: #ffb80033;
  color: #ffb800;
}
.badge.critical {
  background: #ff6b6b33;
  color: #ff6b6b;
}
</style>
