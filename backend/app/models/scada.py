"""SCADA 数据模型"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StationMetrics(BaseModel):
    """电站实时指标"""
    station_id: str
    timestamp: datetime
    power_kw: float | None = None
    irradiance: float | None = None
    wind_speed: float | None = None
    temperature: float | None = None
    humidity: float | None = None
    status: str = "normal"


class Alert(BaseModel):
    """告警记录"""
    id: int | None = None
    station_id: str
    alert_type: str
    level: str  # warning / critical
    message: str
    timestamp: datetime
    resolved: bool = False


class QueryRequest(BaseModel):
    """自然语言查询请求"""
    question: str
    station_id: str | None = None
    time_range: str = "24h"  # 1h / 24h / 7d / 30d


class ChartData(BaseModel):
    """图表数据响应"""
    title: str
    chart_type: str  # line / bar / scatter / pie
    labels: list[str]
    datasets: list[dict[str, Any]]
    sql: str = ""
