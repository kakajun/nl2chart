"""SCADA 数据路由"""

from fastapi import APIRouter, HTTPException

from app.db.tdengine import get_td_client
from app.models.scada import Alert, ChartData, QueryRequest, StationMetrics

router = APIRouter(prefix="/api/scada", tags=["scada"])


@router.get("/stations", summary="获取电站列表")
async def list_stations():
    with get_td_client() as db:
        rows = db.query(
            "SELECT DISTINCT station_id FROM device_data LIMIT 100"
        )
        return {"stations": [r["station_id"] for r in rows]}


@router.get("/metrics/{station_id}", summary="电站实时指标")
async def station_metrics(station_id: str):
    with get_td_client() as db:
        sql = f"""SELECT LAST(power_kw) as power_kw,
                          LAST(irradiance) as irradiance,
                          LAST(wind_speed) as wind_speed,
                          LAST(temperature) as temperature,
                          LAST(humidity) as humidity
                   FROM device_data
                   WHERE station_id = '{station_id}'"""
        rows = db.query(sql)
        if not rows:
            raise HTTPException(status_code=404, detail="Station not found")
        return {"station_id": station_id, **rows[0]}


@router.get("/history/{station_id}", summary="历史趋势数据")
async def history_data(
    station_id: str,
    metric: str = "power_kw",
    hours: int = 24,
    interval: str = "1h",
):
    with get_td_client() as db:
        sql = f"""SELECT _iwt as ts, AVG({metric}) as val
                   FROM device_data
                   WHERE station_id = '{station_id}'
                     AND ts >= NOW() - {hours}h
                   INTERVAL({interval})"""
        rows = db.query(sql)
        labels = [str(r["ts"]) for r in rows]
        values = [r["val"] for r in rows]
        return ChartData(
            title=f"{station_id} — {metric} ({hours}h)",
            chart_type="line",
            labels=labels,
            datasets=[{"label": metric, "data": values}],
            sql=sql,
        )


@router.get("/alerts", summary="告警列表")
async def list_alerts(station_id: str | None = None, limit: int = 50):
    where = f"WHERE station_id = '{station_id}'" if station_id else ""
    with get_td_client() as db:
        sql = f"SELECT * FROM alerts {where} ORDER BY ts DESC LIMIT {limit}"
        rows = db.query(sql)
        return {"alerts": rows}


@router.post("/query", summary="自然语言查询")
async def nl_query(req: QueryRequest):
    # TODO: 接入 LLM 做 Text2SQL
    return {"question": req.question, "sql": "-- TODO: LLM generation", "result": []}
