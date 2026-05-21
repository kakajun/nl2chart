from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

import json
from pathlib import Path

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from app.db.point_map import MODEL_POINT_MAP

router = APIRouter(prefix="/api/scada", tags=["scada"])

DB_PATH = Path(__file__).parent.parent / "db" / "mock_scada.db"

# 加载测点分类配置
POINT_TREE_PATH = Path(__file__).parent.parent / "db" / "point_map_full.json"
POINT_TREE = {}
if POINT_TREE_PATH.exists():
    with open(POINT_TREE_PATH, "r", encoding="utf-8") as f:
        POINT_TREE = json.load(f)


def get_db():
    return sqlite3.connect(DB_PATH)


@router.get("/stations", summary="获取电站列表")
async def list_stations():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT DISTINCT station_code FROM scada_data")
    rows = c.fetchall()
    conn.close()
    return {"stations": [r[0] for r in rows]}


@router.get("/metrics/{station_code}", summary="电站实时指标")
async def station_metrics(station_code: str):
    conn = get_db()
    c = conn.cursor()

    # 获取最新数据
    c.execute("""
        SELECT equ_code, point_code, point_name, value
        FROM scada_data
        WHERE station_code = ? AND ts = (
            SELECT MAX(ts) FROM scada_data WHERE station_code = ?
        )
    """, (station_code, station_code))
    rows = c.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="Station not found")

    # 按测点类型分组
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


@router.get("/history/{station_code}", summary="历史趋势数据")
async def history_data(
    station_code: str,
    metric: str = "irradiance",
    hours: int = 24,
    points: str = None,
    range: str = "24h",
):
    conn = get_db()
    c = conn.cursor()

    # 解析时间范围
    if range.endswith("h"):
        hours = int(range[:-1])
        time_sql = f"ts >= datetime('now', '-{hours} hours')"
    elif range.endswith("d"):
        days = int(range[:-1])
        time_sql = f"ts >= datetime('now', '-{days} days')"
    else:
        time_sql = f"ts >= datetime('now', '-24 hours')"

    # 如果传了points参数，按points查询
    if points:
        point_codes = [p.strip() for p in points.split(",")]
        placeholders = ",".join(["?"] * len(point_codes))
        
        # 获取测点名称
        c.execute(f"""
            SELECT DISTINCT point_code, point_name
            FROM scada_data
            WHERE station_code = ? AND point_code IN ({placeholders})
        """, (station_code, *point_codes))
        name_map = {r[0]: r[1] for r in c.fetchall()}
        
        # 查询每个测点的数据
        all_series = []
        labels = []
        
        for pcode in point_codes:
            c.execute(f"""
                SELECT ts, value
                FROM scada_data
                WHERE station_code = ? AND point_code = ? AND {time_sql}
                ORDER BY ts
            """, (station_code, pcode))
            rows = c.fetchall()
            
            if rows:
                if not labels:
                    labels = [r[0] for r in rows]
                values = [r[1] for r in rows]
                all_series.append({
                    "name": name_map.get(pcode, pcode),
                    "data": values,
                })
        
        conn.close()
        return {
            "title": f"{station_code} 趋势",
            "labels": labels,
            "series": all_series,
        }

    # 否则按metric关键词查询
    point_keyword = {
        "irradiance": "辐射",
        "temperature": "环温",
        "wind_speed": "风速",
        "humidity": "湿",
        "power_kw": "有功功率",
    }.get(metric, metric)

    c.execute(f"""
        SELECT ts, AVG(value) as val
        FROM scada_data
        WHERE station_code = ? AND point_name LIKE ?
          AND {time_sql}
        GROUP BY strftime('%Y-%m-%d %H:%M', ts)
        ORDER BY ts
    """, (station_code, f"%{point_keyword}%"))

    rows = c.fetchall()
    conn.close()

    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]

    return {
        "title": f"{station_code} — {metric}",
        "chart_type": "line",
        "labels": labels,
        "datasets": [{"label": metric, "data": values}],
        "series": [{"name": metric, "data": values}],
    }


@router.get("/alerts", summary="告警列表")
async def list_alerts(station_code: Optional[str] = None, limit: int = 50):
    conn = get_db()
    c = conn.cursor()

    if station_code:
        c.execute(
            "SELECT * FROM alerts WHERE station_code = ? ORDER BY ts DESC LIMIT ?",
            (station_code, limit),
        )
    else:
        c.execute("SELECT * FROM alerts ORDER BY ts DESC LIMIT ?", (limit,))

    rows = c.fetchall()
    conn.close()

    alerts = []
    for row in rows:
        alerts.append({
            "id": row[0],
            "ts": row[1],
            "station_code": row[2],
            "equ_code": row[3],
            "alert_type": row[4],
            "level": row[5],
            "message": row[6],
            "resolved": row[7],
        })

    return {"alerts": alerts}


@router.get("/points/{station_code}", summary="获取电站测点列表")
async def list_points(station_code: str):
    """返回电站下所有设备的测点映射"""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT equ_code, equ_model, equ_type
        FROM scada_data
        WHERE station_code = ?
    """, (station_code,))
    rows = c.fetchall()
    conn.close()

    result = []
    for equ_code, equ_model, equ_type in rows:
        points = MODEL_POINT_MAP.get(equ_model, {})
        result.append({
            "equ_code": equ_code,
            "equ_model": equ_model,
            "equ_type": equ_type,
            "points": [{"code": k, "name": v} for k, v in points.items()],
        })

    return {"station_code": station_code, "devices": result}


@router.get("/point-tree", summary="获取测点分类树")
async def point_tree(station: str = "HBZ"):
    """返回分类后的测点树结构"""
    if POINT_TREE.get("station_code") == station:
        return {"station": station, "categories": POINT_TREE.get("categories", [])}
    
    # 如果没有配置文件，从数据库动态生成
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT point_code, point_name
        FROM scada_data
        WHERE station_code = ?
    """, (station,))
    rows = c.fetchall()
    conn.close()
    
    # 按名称分类
    categories = {}
    for code, name in rows:
        if "环境监测" in name:
            cat = "环境监测"
        elif "直流充电" in name or "充电屏" in name:
            cat = "直流系统"
        elif "逆变器" in name:
            cat = "逆变器"
        elif "箱变" in name or "变压器" in name:
            cat = "箱变/变压器"
        elif "保护" in name or "测控" in name:
            cat = "保护测控"
        elif "汇流箱" in name:
            cat = "汇流箱"
        elif "集电线" in name:
            cat = "集电线"
        else:
            cat = "其他"
        
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({"code": code, "name": name.replace(cat, "").strip("1#"), "unit": ""})
    
    cat_list = [{"id": f"cat{i}", "name": k, "points": v} for i, (k, v) in enumerate(sorted(categories.items(), key=lambda x: -len(x[1])))]
    return {"station": station, "categories": cat_list}


@router.get("/correlation/{station_code}", summary="相关性分析")
async def correlation(
    station_code: str,
    x: str = "irradiance",
    y: str = "power",
    range: str = "24h",
):
    """分析两个指标的相关性（散点图数据）"""
    conn = get_db()
    c = conn.cursor()

    # 解析时间范围
    if range.endswith("h"):
        hours = int(range[:-1])
        time_sql = f"ts >= datetime('now', '-{hours} hours')"
    elif range.endswith("d"):
        days = int(range[:-1])
        time_sql = f"ts >= datetime('now', '-{days} days')"
    else:
        time_sql = f"ts >= datetime('now', '-24 hours')"

    # 查找x对应的测点
    x_keyword = {"irradiance": "辐射", "power": "功率", "temperature": "温度"}.get(x, x)
    y_keyword = {"irradiance": "辐射", "power": "功率", "temperature": "温度"}.get(y, y)

    # 获取两个测点的数据，按时间对齐
    c.execute(f"""
        SELECT ts, point_code, value
        FROM scada_data
        WHERE station_code = ? 
          AND (point_name LIKE ? OR point_name LIKE ?)
          AND {time_sql}
        ORDER BY ts
    """, (station_code, f"%{x_keyword}%", f"%{y_keyword}%"))
    
    rows = c.fetchall()
    conn.close()

    # 简化处理：找两个代表性的测点
    point_data = defaultdict(list)
    for ts, pcode, val in rows:
        point_data[pcode].append((ts, val))

    # 找数据最多的两个测点
    top_points = sorted(point_data.keys(), key=lambda k: len(point_data[k]), reverse=True)[:2]
    
    if len(top_points) < 2:
        return {"points": [], "correlation": 0}

    # 按时间对齐
    x_data = {ts: val for ts, val in point_data[top_points[0]]}
    y_data = {ts: val for ts, val in point_data[top_points[1]]}
    
    common_ts = sorted(set(x_data.keys()) & set(y_data.keys()))
    scatter = []
    for ts in common_ts:
        scatter.append([x_data[ts], y_data[ts]])

    return {
        "x_label": x,
        "y_label": y,
        "x_point": top_points[0],
        "y_point": top_points[1],
        "points": scatter[:1000],  # 限制数据量
        "count": len(scatter),
    }


class QueryRequest(BaseModel):
    question: str


@router.post("/query", summary="自然语言查询")
async def nl_query(req: QueryRequest):
    # TODO: 接入 LLM 做 Text2SQL
    return {"question": req.question, "sql": "-- TODO: LLM generation", "result": []}
