<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>测点导航</h2>
      </div>
      <PointTree :categories="pointCategories" @select="onPointSelect" />
    </aside>

    <main class="main">
      <header class="header">
        <h1>新能源 SCADA 监控中心</h1>
        <div class="header-right">
          <span class="station-tag">HBZ 电站</span>
          <span class="status" :class="{ online: connected }">
            {{ connected ? "数据在线" : "连接中断" }}
          </span>
        </div>
      </header>

      <div class="time-bar">
        <span class="time-label">时间范围:</span>
        <button
          v-for="r in timeRanges"
          :key="r.value"
          class="time-btn"
          :class="{ active: timeRange === r.value }"
          @click="setTimeRange(r.value)"
        >
          {{ r.label }}
        </button>
      </div>

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
        <div class="chart-panel wide">
          <div class="panel-header">
            <h3>趋势分析</h3>
            <span v-if="selectedPoints.length > 0" class="panel-subtitle">
              {{ selectedPoints.map((p) => p.name).join(", ") }}
            </span>
          </div>
          <v-chart class="chart" :option="trendOption" autoresize />
        </div>
      </div>

      <div class="charts-row">
        <div class="chart-panel">
          <h3>辐照度 / 功率对比</h3>
          <v-chart class="chart" :option="correlationOption" autoresize />
        </div>
        <div class="chart-panel">
          <h3>实时测点数据</h3>
          <div class="point-grid">
            <div
              v-for="pt in latestPoints.slice(0, 12)"
              :key="pt.point_code"
              class="point-cell"
            >
              <span class="pt-name">{{ pt.point_name }}</span>
              <span class="pt-value" :style="{ color: getValueColor(pt) }">
                {{ pt.value?.toFixed ? pt.value.toFixed(1) : pt.value }}
              </span>
              <span class="pt-unit">{{ getUnit(pt.point_name) }}</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart, ScatterChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  ToolboxComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import MetricCard from "./MetricCard.vue";
import PointTree from "./PointTree.vue";

use([
  CanvasRenderer,
  LineChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  ToolboxComponent,
]);

const API_BASE = import.meta.env.VITE_API_BASE || "";

const connected = ref(false);
const timeRange = ref("24h");
const timeRanges = [
  { label: "1小时", value: "1h" },
  { label: "6小时", value: "6h" },
  { label: "24小时", value: "24h" },
  { label: "3天", value: "3d" },
  { label: "7天", value: "7d" },
];

const metrics = ref([
  { key: "power", title: "实时功率", value: "--", unit: "kW", color: "#00d26a" },
  { key: "irradiance", title: "辐照度", value: "--", unit: "W/m²", color: "#ffb800" },
  { key: "temp", title: "环境温度", value: "--", unit: "°C", color: "#ff6b6b" },
  { key: "wind", title: "风速", value: "--", unit: "m/s", color: "#4dabf7" },
]);

const pointCategories = ref([]);
const selectedPoints = ref([]);
const latestPoints = ref([]);

const trendOption = ref({
  tooltip: { trigger: "axis", confine: true },
  legend: { data: [], textStyle: { color: "#94a3b8" } },
  grid: { left: 50, right: 30, top: 40, bottom: 60 },
  toolbox: {
    feature: {
      dataZoom: {},
      restore: {},
      saveAsImage: {},
    },
    iconStyle: { borderColor: "#64748b" },
  },
  dataZoom: [{ type: "inside" }, { type: "slider", bottom: 10 }],
  xAxis: {
    type: "category",
    data: [],
    axisLine: { lineStyle: { color: "#374151" } },
    axisLabel: { color: "#94a3b8" },
  },
  yAxis: {
    type: "value",
    axisLine: { lineStyle: { color: "#374151" } },
    axisLabel: { color: "#94a3b8" },
    splitLine: { lineStyle: { color: "#1e293b" } },
  },
  series: [],
});

const correlationOption = ref({
  tooltip: { trigger: "item", formatter: (p) => `${p.data[0]}, ${p.data[1]}` },
  grid: { left: 50, right: 30, top: 20, bottom: 30 },
  xAxis: {
    type: "value",
    name: "辐照度 W/m²",
    axisLine: { lineStyle: { color: "#374151" } },
    axisLabel: { color: "#94a3b8" },
    splitLine: { lineStyle: { color: "#1e293b" } },
  },
  yAxis: {
    type: "value",
    name: "功率 kW",
    axisLine: { lineStyle: { color: "#374151" } },
    axisLabel: { color: "#94a3b8" },
    splitLine: { lineStyle: { color: "#1e293b" } },
  },
  series: [
    {
      type: "scatter",
      data: [],
      symbolSize: 6,
      itemStyle: { color: "#00d26a" },
    },
  ],
});

function getUnit(name) {
  if ("辐射" in name) return "W/m²";
  if ("温度" in name) return "°C";
  if ("湿度" in name) return "%";
  if ("风速" in name) return "m/s";
  if ("风向" in name) return "°";
  if ("气压" in name) return "hPa";
  if ("电压" in name) return "V";
  if ("电流" in name) return "A";
  if ("功率" in name) return "kW";
  if ("电度" in name) return "kWh";
  return "";
}

function getValueColor(pt) {
  const name = pt.point_name || "";
  if ("辐射" in name) return "#ffb800";
  if ("温度" in name) return "#ff6b6b";
  if ("功率" in name || "电度" in name) return "#00d26a";
  return "#e0e6ed";
}

async function loadPointTree() {
  try {
    const res = await fetch(`${API_BASE}/api/scada/point-tree?station=HBZ`);
    const data = await res.json();
    pointCategories.value = data.categories || [];
  } catch (e) {
    console.error("加载测点树失败", e);
  }
}

async function fetchMetrics(stationCode = "HBZ") {
  try {
    const res = await fetch(`${API_BASE}/api/scada/metrics/${stationCode}`);
    const data = await res.json();
    metrics.value[0].value = data.power_kw?.toFixed(1) ?? "--";
    metrics.value[1].value = data.irradiance?.toFixed(1) ?? "--";
    metrics.value[2].value = data.temperature?.toFixed(1) ?? "--";
    metrics.value[3].value = data.wind_speed?.toFixed(1) ?? "--";
    latestPoints.value = data.latest_points || [];
    connected.value = true;
  } catch {
    connected.value = false;
  }
}

async function fetchTrend(points, range = "24h") {
  if (!points.length) return;
  try {
    const codes = points.map((p) => p.code).join(",");
    const res = await fetch(
      `${API_BASE}/api/scada/history/HBZ?points=${codes}&range=${range}`,
    );
    const data = await res.json();

    trendOption.value.legend.data = data.series.map((s) => s.name);
    trendOption.value.xAxis.data = data.labels;
    trendOption.value.series = data.series.map((s) => ({
      name: s.name,
      type: "line",
      smooth: true,
      data: s.data,
      showSymbol: false,
    }));
  } catch (e) {
    console.error("趋势数据加载失败", e);
  }
}

async function fetchCorrelation(range = "24h") {
  try {
    const res = await fetch(
      `${API_BASE}/api/scada/correlation/HBZ?x=irradiance&y=power&range=${range}`,
    );
    const data = await res.json();
    correlationOption.value.series[0].data = data.points || [];
  } catch {
    // silent
  }
}

function setTimeRange(range) {
  timeRange.value = range;
  fetchTrend(selectedPoints.value, range);
  fetchCorrelation(range);
}

function onPointSelect(points) {
  selectedPoints.value = points;
  fetchTrend(points, timeRange.value);
}

watch(timeRange, (range) => {
  fetchTrend(selectedPoints.value, range);
  fetchCorrelation(range);
});

onMounted(() => {
  loadPointTree();
  fetchMetrics("HBZ");
  fetchCorrelation("24h");
  setInterval(() => fetchMetrics("HBZ"), 10000);
});
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  background: #0a0e1a;
  color: #e0e6ed;
}
.sidebar {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid #1e293b;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #1e293b;
}
.sidebar-header h2 {
  margin: 0;
  font-size: 14px;
  color: #94a3b8;
}
.main {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.header h1 {
  margin: 0;
  font-size: 20px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.station-tag {
  padding: 4px 12px;
  background: #1e293b;
  border-radius: 4px;
  font-size: 12px;
  color: #94a3b8;
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
.time-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.time-label {
  font-size: 13px;
  color: #64748b;
}
.time-btn {
  padding: 4px 12px;
  border: 1px solid #374151;
  background: transparent;
  color: #94a3b8;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.time-btn.active {
  background: #4dabf7;
  border-color: #4dabf7;
  color: #fff;
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
.chart-panel.wide {
  grid-column: 1 / -1;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.panel-header h3 {
  margin: 0;
  font-size: 14px;
  color: #94a3b8;
}
.panel-subtitle {
  font-size: 12px;
  color: #64748b;
}
.chart {
  height: 300px;
}
.point-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}
.point-cell {
  background: #0a0e1a;
  border-radius: 6px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.pt-name {
  font-size: 11px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pt-value {
  font-size: 16px;
  font-weight: 600;
  font-family: monospace;
}
.pt-unit {
  font-size: 10px;
  color: #64748b;
}
</style>
