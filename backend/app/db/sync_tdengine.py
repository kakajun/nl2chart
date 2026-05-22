"""数据同步器 — 从 TDengine 拉取真实数据到本地 SQLite 缓存"""

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.tdengine_real import TDEngineClient, check_tdengine
from app.db.point_map import MODEL_POINT_MAP

DB_PATH = Path(__file__).parent / "mock_scada.db"


def init_cache_db():
    """初始化本地缓存数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS scada_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            station_code TEXT,
            equ_code TEXT,
            equ_model TEXT,
            equ_type TEXT,
            point_code TEXT,
            point_name TEXT,
            value REAL
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_ts ON scada_data(ts)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_station ON scada_data(station_code)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_point ON scada_data(point_code)")
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
    conn.commit()
    conn.close()
    print("[Sync] 缓存数据库已初始化")


def sync_from_tdengine(
    table_name: str = "hbz_yc",
    hours: int = 48,
    station_code: str = "HBZ",
):
    """从 TDengine 同步最近 N 小时的数据到本地 SQLite"""
    print(f"[Sync] 开始同步 {table_name} 最近 {hours} 小时数据...")

    client = TDEngineClient(use_zt=True)
    if not client.connect():
        client = TDEngineClient(use_zt=False)
        if not client.connect():
            print("[Sync] ❌ TDengine 连接失败，无法同步")
            return False

    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        # 查询数据
        data = client.query_station_data(
            table_name=table_name,
            start_time=start_time,
            end_time=end_time,
        )

        if not data:
            print("[Sync] ⚠️ 未获取到数据")
            return False

        print(f"[Sync] 从 TDengine 获取到 {len(data)} 条记录")

        # 加载测点名称映射
        point_map = {}
        for model, points in MODEL_POINT_MAP.items():
            point_map.update(points)

        # 写入 SQLite
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 清空该时间段旧数据（避免重复）
        c.execute("""
            DELETE FROM scada_data
            WHERE station_code = ? AND ts >= ?
        """, (station_code, start_time.strftime("%Y-%m-%d %H:%M:%S")))
        deleted = c.rowcount
        print(f"[Sync] 清除了 {deleted} 条旧缓存数据")

        # 插入新数据
        inserted = 0
        for row in data:
            pcode = row.get("point_code", "")
            pname = point_map.get(pcode, pcode)
            c.execute("""
                INSERT INTO scada_data
                (ts, station_code, equ_code, equ_model, equ_type, point_code, point_name, value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row.get("ts", ""),
                station_code,
                row.get("equ_code", "HBZ"),
                "hbz",
                "real",
                pcode,
                pname,
                row.get("value", 0),
            ))
            inserted += 1

        conn.commit()
        conn.close()

        print(f"[Sync] ✅ 成功写入 {inserted} 条记录到本地缓存")
        return True

    except Exception as e:
        print(f"[Sync] ❌ 同步失败: {e}")
        return False

    finally:
        client.close()


def get_data_source():
    """判断当前数据源"""
    status = check_tdengine()
    if status["connected"]:
        return "tdengine", status
    else:
        # 检查本地缓存是否有数据
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM scada_data")
        count = c.fetchone()[0]
        conn.close()
        if count > 0:
            return "cache", {"count": count, "message": "使用本地缓存数据"}
        return "mock", {"message": "使用 mock 数据"}


if __name__ == "__main__":
    print("=" * 50)
    print("SCADA 数据同步工具")
    print("=" * 50)

    # 检查数据源
    source, info = get_data_source()
    print(f"当前数据源: {source}")
    if source == "tdengine":
        print(f"TDengine 状态: ✅ 在线")
        print(f"可用表: {info['table_count']} 个")
    elif source == "cache":
        print(f"本地缓存: {info['count']} 条记录")
    else:
        print(f"使用 mock 数据")

    # 初始化数据库
    init_cache_db()

    # 如果 TDengine 在线，执行同步
    if source == "tdengine":
        print("\n开始同步...")
        sync_from_tdengine(hours=72)
    else:
        print("\nTDengine 不在线，跳过同步")
        print("提示: 检查 ZeroTier 网络或 TDengine 服务状态")

    print("=" * 50)
