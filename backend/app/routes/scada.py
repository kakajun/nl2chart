from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from app.db.point_map import MODEL_POINT_MAP

router = APIRouter(prefix="/api/scada", tags=["scada"])

DB_PATH = Path(__file__).parent.parent / "db" / "mock_scada.db"


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
    for equ_code, pcode, pname, val in rows:
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

    return {"station_code": station_code, **metrics}


@router.get("/history/{station_code}", summary="历史趋势数据")
async def history_data(
    station_code: str,
    metric: str = "irradiance",
    hours: int = 24,
):
    conn = get_db()
    c = conn.cursor()

    # 查找对应测点
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
    conn.close()

    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]

    return {
        "title": f"{station_code} — {metric} ({hours}h)",
        "chart_type": "line",
        "labels": labels,
        "datasets": [{"label": metric, "data": values}],
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


class QueryRequest(BaseModel):
    question: str


@router.post("/query", summary="自然语言查询")
async def nl_query(req: QueryRequest):
    # TODO: 接入 LLM 做 Text2SQL
    return {"question": req.question, "sql": "-- TODO: LLM generation", "result": []}
