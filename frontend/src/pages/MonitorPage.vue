<template>
  <div class="monitor-page">
    <div class="monitor-center">
      <header class="page-header">
        <h1>新能源 SCADA 监控中心</h1>
        <div class="header-right">
          <span class="station-tag">HBZ 电站</span>
          <span class="status" :class="{ online: connected }">
            {{ connected ? "数据在线" : "连接中断" }}
          </span>
        </div>
      </header>

      <div class="metric-row">
        <MetricCard
          v-for="m in metrics"
          :key="m.key"
          :title="m.title"
          :value="m.value"
          :unit="m.unit"
          :color="m.color"
        />
      </div>

      <div class="chart-section">
        <div class="chart-main">
          <div class="panel-header">
            <h3>趋势分析</h3>
            <div class="time-bar">
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
          </div>
          <v-chart class="chart" :option="trendOption" autoresize />
        </div>
      </div>

      <div class="chart-row-2">
        <div class="chart-sub">
          <h3>辐照度 / 功率对比</h3>
          <v-chart class="chart" :option="correlationOption" autoresize />
        </div>
        <div class="chart-sub">
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
    </div>

    <aside class="monitor-right">
      <PointTree :categories="pointCategories" @select="onPointSelect" />
    </aside>
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
import MetricCard from "../components/MetricCard.vue";
import PointTree from "../components/PointTree.vue";

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
  { label: "1h", value: "1h" },
  { label: "6h", value: "6h" },
  { label: "24h", value: "24h" },
  { label: "3d", value: "3d" },
  { label: "7d", value: "7d" },
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
    feature: { dataZoom: {}, restore: {}, saveAsImage: {} },
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
    { type: "scatter", data: [], symbolSize: 6, itemStyle: { color: "#00d26a" } },
  ],
});

function getUnit(name) {
  if (!name) return "";
  if (name.includes("辐射")) return "W/m²";
  if (name.includes("温度")) return "°C";
  if (name.includes("湿度")) return "%";
  if (name.includes("风速")) return "m/s";
  if (name.includes("风向")) return "°";
  if (name.includes("气压")) return "hPa";
  if (name.includes("电压")) return "V";
  if (name.includes("电流")) return "A";
  if (name.includes("功率")) return "kW";
  if (name.includes("电度")) return "kWh";
  return "";
}

function getValueColor(pt) {
  const name = pt.point_name || "";
  if (name.includes("辐射")) return "#ffb800";
  if (name.includes("温度")) return "#ff6b6b";
  if (name.includes("功率") || name.includes("电度")) return "#00d26a";
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
  } catch {}
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
.monitor-page {
  display: flex;
  height: 100%;
  gap: 16px;
}
.monitor-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  min-width: 0;
}
.monitor-right {
  width: 280px;
  flex-shrink: 0;
  background: #111827;
  border-radius: 8px;
  overflow: hidden;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}
.page-header h1 {
  margin: 0;
  font-size: 18px;
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
.metric-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.chart-section {
  background: #111827;
  border-radius: 8px;
  padding: 12px;
}
.chart-main {
  height: 320px;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.panel-header h3 {
  margin: 0;
  font-size: 14px;
  color: #94a3b8;
}
.time-bar {
  display: flex;
  gap: 6px;
}
.time-btn {
  padding: 3px 10px;
  border: 1px solid #374151;
  background: transparent;
  color: #94a3b8;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
}
.time-btn.active {
  background: #4dabf7;
  border-color: #4dabf7;
  color: #fff;
}
.chart {
  height: 260px;
}
.chart-row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.chart-sub {
  background: #111827;
  border-radius: 8px;
  padding: 12px;
}
.chart-sub h3 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #94a3b8;
}
.point-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  max-height: 240px;
  overflow-y: auto;
}
.point-cell {
  background: #0a0e1a;
  border-radius: 6px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.pt-name {
  font-size: 10px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pt-value {
  font-size: 15px;
  font-weight: 600;
  font-family: monospace;
}
.pt-unit {
  font-size: 9px;
  color: #64748b;
}
</style>
