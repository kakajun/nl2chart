"""数据适配器 — 统一 mock / 缓存 / TDengine 真实数据源"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

from tdengine_real import TDEngineClient, check_tdengine
from point_map import MODEL_POINT_MAP

DB_PATH = Path(__file__).parent / "mock_scada.db"


class DataAdapter:
    """数据适配器 — 自动选择最佳数据源"""

    def __init__(self):
        self._td_client = None
        self._td_available = None  # None=未检测, True=可用, False=不可用
        self._mock_conn = None
        # 按设备模型分别存储测点映射
        self._model_maps = MODEL_POINT_MAP
        # 默认通用映射（many1.x 优先，dq补充）
        self._point_map = {}
        for model, points in MODEL_POINT_MAP.items():
            if model.startswith('many'):
                self._point_map.update(points)
        # dq模型补充不重叠的编码
        for code, name in MODEL_POINT_MAP.get('dq', {}).items():
            if code not in self._point_map:
                self._point_map[code] = name

    def _get_point_name(self, equ_code: str, pcode: str) -> str:
        """根据设备编码和测点编码返回正确的测点名称"""
        # 去掉 HBZ_ 前缀
        if equ_code.startswith('HBZ_'):
            equ_code = equ_code[4:]
        # HJ01 = 环境监测仪 → dq模型
        if equ_code == 'HJ01':
            return MODEL_POINT_MAP.get('dq', {}).get(pcode, self._point_map.get(pcode, pcode))
        # F1/F2/F3 = 箱变测控 → many1.0模型
        if equ_code in ('F1', 'F2', 'F3'):
            return MODEL_POINT_MAP.get('many1.0', {}).get(pcode, self._point_map.get(pcode, pcode))
        # 默认使用通用映射
        return self._point_map.get(pcode, pcode)

    @property
    def td_available(self) -> bool:
        if self._td_available is None:
            status = check_tdengine()
            self._td_available = status["connected"]
            if self._td_available and self._td_client is None:
                self._td_client = TDEngineClient()
                self._td_client.connect()
        return self._td_available

    def _get_mock_conn(self):
        if self._mock_conn is None:
            self._mock_conn = sqlite3.connect(DB_PATH)
        return self._mock_conn

    def get_latest(self, station_code: str = "HBZ") -> Dict:
        """获取最新数据"""
        # 优先尝试 TDengine
        if self.td_available:
            try:
                data = self._fetch_latest_tdengine(station_code)
                if data:
                    return {**data, "source": "tdengine"}
            except Exception as e:
                print(f"[Adapter] TDengine 获取最新数据失败: {e}")

        # 回退到本地缓存 / mock
        return {**self._fetch_latest_mock(station_code), "source": "mock"}

    def get_history(
        self,
        station_code: str,
        metric: str = None,
        point_codes: List[str] = None,
        hours: int = 24,
        range_str: str = "24h",
    ) -> Dict:
        """获取历史数据"""
        if self.td_available:
            try:
                data = self._fetch_history_tdengine(station_code, point_codes, range_str)
                if data:
                    return {**data, "source": "tdengine"}
            except Exception as e:
                print(f"[Adapter] TDengine 获取历史数据失败: {e}")

        return {**self._fetch_history_mock(station_code, metric, hours), "source": "mock"}

    def _fetch_latest_tdengine(self, station_code: str) -> Dict:
        """从 TDengine 获取最新数据"""
        if not self._td_client:
            return {}

        # 查询超级表最新数据
        data = self._td_client.query_station_data(
            table_name="stable_es_station_pjygcdz_equ",
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now(),
        )

        if not data:
            return {}

        # 获取最新时间点
        latest_ts = max([row["ts"] for row in data if row.get("ts")])
        latest_rows = [r for r in data if r.get("ts") == latest_ts]

        metrics = {}
        latest_points = []
        for row in latest_rows:
            pcode = row.get("point_code", "")
            equ_code = row.get("equ_code", station_code)
            pname = self._get_point_name(equ_code, pcode)
            val = row.get("value", 0)
            latest_points.append({
                "equ_code": equ_code,
                "point_code": pcode,
                "point_name": pname,
                "value": val,
            })
            # 只取环境监测仪(HJ01)的数据作为KPI
            if equ_code == "HJ01":
                if "辐射" in pname and "平均" not in pname and "累计" not in pname:
                    metrics["irradiance"] = val
                elif "环温" in pname or ("温度" in pname and "平均" not in pname):
                    metrics["temperature"] = val
                elif "风速" in pname and "平均" not in pname:
                    metrics["wind_speed"] = val
                elif "环湿" in pname or ("湿度" in pname and "平均" not in pname):
                    metrics["humidity"] = val

        return {
            "station_code": station_code,
            "latest_points": latest_points[:50],
            **metrics,
        }

    def _fetch_latest_mock(self, station_code: str) -> Dict:
        """从本地 SQLite 获取最新数据"""
        conn = self._get_mock_conn()
        c = conn.cursor()
        c.execute("""
            SELECT equ_code, point_code, point_name, value
            FROM scada_data
            WHERE station_code = ? AND ts = (
                SELECT MAX(ts) FROM scada_data WHERE station_code = ?
            )
        """, (station_code, station_code))
        rows = c.fetchall()

        if not rows:
            return {"station_code": station_code, "latest_points": []}

        metrics = {}
        latest_points = []
        for equ_code, pcode, pname, val in rows:
            latest_points.append({
                "equ_code": equ_code,
                "point_code": pcode,
                "point_name": pname,
                "value": val,
            })
            if "辐射" in pname and "平均" not in pname and "累计" not in pname:
                metrics["irradiance"] = val
            elif "环温" in pname or "温度" in pname:
                metrics["temperature"] = val
            elif "风速" in pname and "平均" not in pname:
                metrics["wind_speed"] = val
            elif "环湿" in pname or "湿度" in pname:
                metrics["humidity"] = val
            elif "功率" in pname and "有功" in pname:
                metrics["power_kw"] = val

        return {
            "station_code": station_code,
            "latest_points": latest_points[:50],
            **metrics,
        }

    def _fetch_history_tdengine(
        self,
        station_code: str,
        point_codes: Optional[List[str]],
        range_str: str,
    ) -> Dict:
        """从 TDengine 获取历史数据"""
        if not self._td_client:
            return {}

        # 解析时间范围
        if range_str.endswith("h"):
            hours = int(range_str[:-1])
            start = datetime.now() - timedelta(hours=hours)
        elif range_str.endswith("d"):
            days = int(range_str[:-1])
            start = datetime.now() - timedelta(days=days)
        else:
            start = datetime.now() - timedelta(hours=24)

        end = datetime.now()

        data = self._td_client.query_station_data(
            table_name="stable_es_station_pjygcdz_equ",
            start_time=start,
            end_time=end,
            point_codes=point_codes,
        )

        if not data:
            return {}

        # 按测点分组
        series_map = {}
        labels = set()
        for row in data:
            ts = str(row.get("ts", ""))
            pcode = row.get("point_code", "")
            pname = self._point_map.get(pcode, pcode)
            val = row.get("value", 0)

            if pname not in series_map:
                series_map[pname] = {}
            series_map[pname][ts] = val
            labels.add(ts)

        sorted_labels = sorted(labels)
        series = []
        for name, values in series_map.items():
            series.append({
                "name": name,
                "data": [values.get(l, None) for l in sorted_labels],
            })

        # 构建equ_code到pcode的映射用于名称解析
        equ_code_map = {}
        for row in data:
            pcode = row.get("point_code", "")
            equ_code = row.get("equ_code", station_code)
            equ_code_map[pcode] = equ_code

        series = []
        for pcode, values in series_map.items():
            equ_code = equ_code_map.get(pcode, station_code)
            pname = self._get_point_name(equ_code, pcode)
            series.append({
                "name": pname,
                "data": [values.get(l, None) for l in sorted_labels],
            })

        return {
            "title": f"{station_code} 趋势",
            "labels": sorted_labels,
            "series": series,
        }

    def _fetch_history_mock(self, station_code: str, metric: str, hours: int) -> Dict:
        """从本地 SQLite 获取历史数据（兼容原有API）"""
        conn = self._get_mock_conn()
        c = conn.cursor()

        point_keyword = {
            "irradiance": "辐射",
            "temperature": "环温",
            "wind_speed": "风速",
            "humidity": "湿",
            "power_kw": "有功功率",
        }.get(metric, metric)

        c.execute("""
            SELECT ts, AVG(value) as val
            FROM scada_data
            WHERE station_code = ? AND point_name LIKE ?
              AND ts >= datetime('now', '-{} hours')
            GROUP BY strftime('%Y-%m-%d %H:%M', ts)
            ORDER BY ts
        """.format(hours), (station_code, f"%{point_keyword}%"))

        rows = c.fetchall()
        labels = [r[0] for r in rows]
        values = [r[1] for r in rows]

        return {
            "title": f"{station_code} — {metric}",
            "chart_type": "line",
            "labels": labels,
            "datasets": [{"label": metric, "data": values}],
            "series": [{"name": metric, "data": values}],
        }


# 全局适配器实例
_adapter: Optional[DataAdapter] = None


def get_adapter() -> DataAdapter:
    global _adapter
    if _adapter is None:
        _adapter = DataAdapter()
    return _adapter


if __name__ == "__main__":
    print("=" * 50)
    print("数据适配器测试")
    print("=" * 50)
    adapter = get_adapter()
    print(f"TDengine 可用: {adapter.td_available}")

    if adapter.td_available:
        print("\n从 TDengine 获取最新数据...")
        data = adapter.get_latest("HBZ")
        print(f"数据点数量: {len(data.get('latest_points', []))}")
        print(f"辐照度: {data.get('irradiance')}")
        print(f"温度: {data.get('temperature')}")
    else:
        print("\n从 Mock 获取最新数据...")
        data = adapter.get_latest("HBZ")
        print(f"数据点数量: {len(data.get('latest_points', []))}")
        print(f"辐照度: {data.get('irradiance')}")

    print("=" * 50)
