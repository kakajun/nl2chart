"""SCADA Mock 数据生成器 — 本地开发用

基于真实测点映射表生成模拟的 SCADA 数据。
运行: python mock_data.py
"""

import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# 导入测点映射表
from point_map import MODEL_POINT_MAP

DB_PATH = Path(__file__).parent / "mock_scada.db"

# 海滨光伏站设备列表 (基于真实配置)
STATIONS = [
    {"code": "hbz", "name": "海滨光伏站", "capacity": 50.0},
]

# 设备列表: (设备编码, 设备模型, 设备类型)
EQUIPS = [
    ("HBZ_HJ01", "dq", "环境监测仪"),
    ("HBZ_F1", "many1.0", "箱变测控"),
    ("HBZ_F2", "many1.1", "箱变测控"),
    ("HBZ_F3", "many1.2", "箱变测控"),
]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS scada_data (
            ts TEXT,
            station_code TEXT,
            equ_code TEXT,
            equ_model TEXT,
            equ_type TEXT,
            point_code TEXT,
            point_name TEXT,
            value REAL,
            PRIMARY KEY (ts, equ_code, point_code)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            station_code TEXT,
            equ_code TEXT,
            alert_type TEXT,
            level TEXT,
            message TEXT,
            resolved INTEGER DEFAULT 0
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_ts ON scada_data(ts)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_station ON scada_data(station_code)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_equ ON scada_data(equ_code)")

    conn.commit()
    return conn


def generate_value(point_name: str, hour: float) -> float:
    """根据测点名和时间生成合理的模拟值"""
    # 辐照度类: 模拟日照曲线
    if "辐射" in point_name or "辐照" in point_name:
        if "累计" in point_name or "时" in point_name:
            return round(random.uniform(0, 100), 2)
        if 6 <= hour <= 18:
            peak = 1000 * (1 - abs(hour - 12) / 6)
            return round(peak + random.gauss(0, 50), 2)
        return 0.0

    # 温度类
    if "温度" in point_name or "温" in point_name:
        return round(random.gauss(25, 8), 2)

    # 湿度类
    if "湿" in point_name:
        return round(random.gauss(65, 15), 2)

    # 风速类
    if "风速" in point_name or "风速" in point_name:
        return round(random.gauss(5, 2), 2)

    # 风向类
    if "风向" in point_name:
        return round(random.uniform(0, 360), 2)

    # 气压类
    if "气压" in point_name:
        return round(random.gauss(1013, 20), 2)

    # 电压类
    if "电压" in point_name:
        if "交流" in point_name or "相" in point_name or "线" in point_name:
            return round(random.gauss(220, 5), 2)
        if "直流" in point_name or "母线" in point_name or "充电" in point_name:
            return round(random.gauss(240, 3), 2)
        if "单体" in point_name:
            return round(random.gauss(2.0, 0.1), 3)
        return round(random.gauss(220, 10), 2)

    # 电流类
    if "电流" in point_name:
        return round(random.gauss(50, 15), 2)

    # 功率类
    if "功率" in point_name or "有功" in point_name or "无功" in point_name:
        return round(random.uniform(0, 500), 2)

    # 功率因数
    if "功率因素" in point_name or "因数" in point_name:
        return round(random.gauss(0.95, 0.05), 3)

    # 频率
    if "频率" in point_name:
        return round(random.gauss(50, 0.2), 2)

    # 电阻/绝缘
    if "电阻" in point_name or "阻抗" in point_name:
        return round(random.gauss(1000, 200), 2)

    # 次数
    if "次数" in point_name:
        return float(random.randint(0, 1000))

    # 容量
    if "容量" in point_name:
        return round(random.gauss(500, 100), 2)

    # 时间
    if "时间" in point_name:
        return round(random.gauss(10, 5), 2)

    # 电量/电度
    if "电量" in point_name or "电度" in point_name:
        return round(random.uniform(0, 10000), 2)

    # 模块类
    if "模块" in point_name:
        if "电压" in point_name:
            return round(random.gauss(240, 2), 2)
        if "电流" in point_name:
            return round(random.gauss(10, 3), 2)
        return round(random.gauss(50, 10), 2)

    # 默认
    return round(random.gauss(50, 20), 2)


def generate_data(hours: int = 24):
    conn = init_db()
    c = conn.cursor()

    now = datetime.now()
    start = now - timedelta(hours=hours)

    # 生成历史数据 — 每5分钟一条
    for equ_code, equ_model, equ_type in EQUIPS:
        # 获取该设备模型的测点映射
        point_map = MODEL_POINT_MAP.get(equ_model, {})
        if not point_map:
            print(f"警告: 设备模型 {equ_model} 无测点映射")
            continue

        ts = start
        while ts <= now:
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            hour = ts.hour + ts.minute / 60

            for pcode, pname in point_map.items():
                val = generate_value(pname, hour)
                c.execute(
                    "INSERT OR REPLACE INTO scada_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (ts_str, "hbz", equ_code, equ_model, equ_type, pcode, pname, val)
                )
            ts += timedelta(minutes=5)

    # 生成告警
    alert_types = ["过压告警", "过流告警", "过温告警", "绝缘告警", "通讯中断", "功率异常"]
    for i in range(20):
        equ = random.choice(EQUIPS)
        atype = random.choice(alert_types)
        level = random.choice(["warning", "critical"])
        ts = start + timedelta(hours=random.randint(0, hours))
        msg = f"{equ[2]} {equ[0]} {atype}"
        c.execute(
            "INSERT INTO alerts (ts, station_code, equ_code, alert_type, level, message) VALUES (?, ?, ?, ?, ?, ?)",
            (ts.strftime("%Y-%m-%d %H:%M:%S"), "hbz", equ[0], atype, level, msg)
        )

    conn.commit()
    conn.close()
    print(f"Mock 数据已生成: {DB_PATH}")
    print(f"  时间范围: {start} ~ {now}")
    print(f"  设备数: {len(EQUIPS)}")
    total_points = sum(len(MODEL_POINT_MAP.get(e[1], {})) for e in EQUIPS)
    print(f"  测点数: {total_points}")


if __name__ == "__main__":
    generate_data(hours=48)
