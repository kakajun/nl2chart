import { createRouter, createWebHashHistory } from "vue-router";
import MonitorPage from "../pages/MonitorPage.vue";
import QueryPage from "../pages/QueryPage.vue";
import AlertPage from "../pages/AlertPage.vue";
import DevicePage from "../pages/DevicePage.vue";
import SettingPage from "../pages/SettingPage.vue";

const routes = [
  { path: "/", redirect: "/monitor" },
  { path: "/monitor", name: "monitor", component: MonitorPage, meta: { title: "SCADA监控", icon: "📊" } },
  { path: "/query", name: "query", component: QueryPage, meta: { title: "数据查询", icon: "🔍" } },
  { path: "/alerts", name: "alerts", component: AlertPage, meta: { title: "告警中心", icon: "🚨" } },
  { path: "/devices", name: "devices", component: DevicePage, meta: { title: "设备管理", icon: "⚙️" } },
  { path: "/settings", name: "settings", component: SettingPage, meta: { title: "系统设置", icon: "🔧" } },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

export default router;
