<template>
  <div class="query-page">
    <header class="page-header">
      <h1>数据查询</h1>
      <p class="desc">选择测点和时间范围，查询历史数据</p>
    </header>
    <div class="query-body">
      <div class="query-left">
        <h3>测点选择</h3>
        <PointTree :categories="pointCategories" @select="onPointSelect" />
      </div>
      <div class="query-main">
        <div class="query-toolbar">
          <div class="toolbar-group">
            <label>时间范围</label>
            <select v-model="timeRange">
              <option value="1h">最近1小时</option>
              <option value="6h">最近6小时</option>
              <option value="24h">最近24小时</option>
              <option value="3d">最近3天</option>
              <option value="7d">最近7天</option>
            </select>
          </div>
          <div class="toolbar-group">
            <label>聚合方式</label>
            <select v-model="aggType">
              <option value="raw">原始值</option>
              <option value="avg">平均值</option>
              <option value="max">最大值</option>
              <option value="min">最小值</option>
            </select>
          </div>
          <button class="btn-query" @click="doQuery" :disabled="!selectedPoints.length">
            查询
          </button>
          <button class="btn-export" @click="exportData" :disabled="!queryResult.length">
            导出CSV
          </button>
        </div>
        <div class="query-result">
          <div v-if="loading" class="loading">查询中...</div>
          <div v-else-if="!queryResult.length" class="empty">请选择测点并点击查询</div>
          <div v-else class="result-table-wrap">
            <table class="result-table">
              <thead>
                <tr>
                  <th>时间</th>
                  <th v-for="s in seriesNames" :key="s">{{ s }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in queryResult.slice(0, 100)" :key="idx">
                  <td>{{ row.time }}</td>
                  <td v-for="s in seriesNames" :key="s">{{ row[s] != null ? row[s].toFixed(2) : '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-if="queryResult.length" class="query-chart">
          <v-chart class="chart" :option="queryChartOption" autoresize />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent, LegendComponent, DataZoomComponent } from "echarts/components";
import VChart from "vue-echarts";
import PointTree from "../components/PointTree.vue";

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent]);

const API_BASE = import.meta.env.VITE_API_BASE || "";

const pointCategories = ref([]);
const selectedPoints = ref([]);
const timeRange = ref("24h");
const aggType = ref("raw");
const loading = ref(false);
const queryResult = ref([]);
const seriesNames = ref([]);

const queryChartOption = computed(() => ({
  tooltip: { trigger: "axis" },
  legend: { data: seriesNames.value, textStyle: { color: "#94a3b8" } },
  grid: { left: 50, right: 30, top: 40, bottom: 60 },
  dataZoom: [{ type: "inside" }, { type: "slider", bottom: 10 }],
  xAxis: {
    type: "category",
    data: queryResult.value.map((r) => r.time),
    axisLine: { lineStyle: { color: "#374151" } },
    axisLabel: { color: "#94a3b8" },
  },
  yAxis: {
    type: "value",
    axisLine: { lineStyle: { color: "#374151" } },
    axisLabel: { color: "#94a3b8" },
    splitLine: { lineStyle: { color: "#1e293b" } },
  },
  series: seriesNames.value.map((name) => ({
    name,
    type: "line",
    smooth: true,
    data: queryResult.value.map((r) => r[name]),
    showSymbol: false,
  })),
}));

async function loadPointTree() {
  try {
    const res = await fetch(`${API_BASE}/api/scada/point-tree?station=HBZ`);
    const data = await res.json();
    pointCategories.value = data.categories || [];
  } catch (e) {
    console.error("加载测点树失败", e);
  }
}

async function doQuery() {
  if (!selectedPoints.value.length) return;
  loading.value = true;
  try {
    const codes = selectedPoints.value.map((p) => p.code).join(",");
    const res = await fetch(
      `${API_BASE}/api/scada/history/HBZ?points=${codes}&range=${timeRange.value}`,
    );
    const data = await res.json();
    seriesNames.value = data.series.map((s) => s.name);
    // pivot to row-based
    const rows = [];
    for (let i = 0; i < data.labels.length; i++) {
      const row = { time: data.labels[i] };
      for (const s of data.series) {
        row[s.name] = s.data[i];
      }
      rows.push(row);
    }
    queryResult.value = rows;
  } catch (e) {
    console.error("查询失败", e);
  } finally {
    loading.value = false;
  }
}

function exportData() {
  const headers = ["时间", ...seriesNames.value];
  const rows = queryResult.value.map((r) => [r.time, ...seriesNames.value.map((s) => r[s] ?? "")]);
  let csv = headers.join(",") + "\n";
  for (const row of rows) {
    csv += row.join(",") + "\n";
  }
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `scada_query_${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
}

function onPointSelect(points) {
  selectedPoints.value = points;
}

onMounted(() => {
  loadPointTree();
});
</script>

<style scoped>
.query-page {
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
.query-body {
  display: flex;
  flex: 1;
  gap: 12px;
  min-height: 0;
}
.query-left {
  width: 260px;
  flex-shrink: 0;
  background: #111827;
  border-radius: 8px;
  padding: 12px;
  overflow-y: auto;
}
.query-left h3 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #94a3b8;
}
.query-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}
.query-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #111827;
  border-radius: 8px;
  padding: 12px;
}
.toolbar-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.toolbar-group label {
  font-size: 11px;
  color: #64748b;
}
.toolbar-group select {
  padding: 6px 10px;
  border: 1px solid #374151;
  background: #0a0e1a;
  color: #e0e6ed;
  border-radius: 4px;
  font-size: 12px;
}
.btn-query {
  padding: 6px 16px;
  border: none;
  background: #4dabf7;
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  margin-left: auto;
}
.btn-query:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-export {
  padding: 6px 16px;
  border: 1px solid #374151;
  background: transparent;
  color: #94a3b8;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}
.btn-export:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.query-result {
  flex: 1;
  background: #111827;
  border-radius: 8px;
  padding: 12px;
  overflow-y: auto;
  min-height: 0;
}
.loading, .empty {
  text-align: center;
  padding: 40px;
  color: #64748b;
  font-size: 14px;
}
.result-table-wrap {
  overflow-x: auto;
}
.result-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.result-table th {
  text-align: left;
  padding: 8px;
  background: #1e293b;
  color: #94a3b8;
  position: sticky;
  top: 0;
}
.result-table td {
  padding: 6px 8px;
  border-bottom: 1px solid #1e293b;
  color: #e0e6ed;
  font-family: monospace;
}
.query-chart {
  height: 240px;
  background: #111827;
  border-radius: 8px;
  padding: 12px;
}
.chart {
  height: 100%;
}
</style>
