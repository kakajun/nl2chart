import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

def generate_extended_mock_data():
    """将mock数据从2天扩充到7天"""
    db_path = Path(__file__).parent / "mock_scada.db"
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    # 获取现有数据的测点列表和最新时间
    c.execute("SELECT DISTINCT point_code, point_name, equ_code FROM scada_data")
    points = c.fetchall()
    
    c.execute("SELECT MAX(ts) FROM scada_data")
    last_ts = c.fetchone()[0]
    last_dt = datetime.strptime(last_ts, "%Y-%m-%d %H:%M:%S")
    
    print(f"现有数据截止: {last_ts}")
    print(f"测点数: {len(points)}")
    
    # 生成后续5天的数据 (直到5月26日)
    target_end = datetime(2026, 5, 26, 16, 24, 22)
    current = last_dt + timedelta(minutes=5)
    
    batch = []
    batch_size = 5000
    total_inserted = 0
    
    # 为每个时间点生成所有测点的数据
    while current <= target_end:
        ts_str = current.strftime("%Y-%m-%d %H:%M:%S")
        
        for point_code, point_name, equ_code in points:
            # 根据测点类型生成合理的值
            if "辐射" in point_name:
                # 辐照度: 0-1200 W/m², 白天有值晚上为0
                hour = current.hour
                if 6 <= hour <= 19:
                    base = 800 if "平均" in point_name else 600
                    value = max(0, base + random.gauss(0, 150))
                else:
                    value = 0
            elif "温度" in point_name or "环温" in point_name:
                value = 15 + random.gauss(0, 5)
            elif "湿度" in point_name or "环湿" in point_name:
                value = 40 + random.gauss(0, 15)
            elif "风速" in point_name:
                value = max(0, 3 + random.gauss(0, 2))
            elif "风向" in point_name:
                value = random.uniform(0, 360)
            elif "气压" in point_name:
                value = 1013 + random.gauss(0, 10)
            elif "电压" in point_name:
                value = 220 + random.gauss(0, 5) if "交流" in point_name else 220 + random.gauss(0, 3)
            elif "电流" in point_name:
                value = max(0, 5 + random.gauss(0, 2))
            elif "功率" in point_name or "无功" in point_name:
                value = random.gauss(0, 50)
            elif "电度" in point_name or "电量" in point_name:
                # 电度是累计值，需要递增
                value = random.uniform(10000, 50000)
            else:
                value = random.gauss(0, 10)
            
            batch.append(("HBZ", equ_code, point_code, point_name, round(value, 2), ts_str))
        
        if len(batch) >= batch_size:
            c.executemany(
                "INSERT INTO scada_data (station_code, equ_code, point_code, point_name, value, ts) VALUES (?, ?, ?, ?, ?, ?)",
                batch
            )
            total_inserted += len(batch)
            print(f"已插入: {total_inserted} 条, 时间: {ts_str}")
            batch = []
        
        current += timedelta(minutes=5)
    
    # 插入剩余批次
    if batch:
        c.executemany(
            "INSERT INTO scada_data (station_code, equ_code, point_code, point_name, value, ts) VALUES (?, ?, ?, ?, ?, ?)",
            batch
        )
        total_inserted += len(batch)
    
    conn.commit()
    
    # 验证
    c.execute("SELECT COUNT(*) FROM scada_data")
    final_count = c.fetchone()[0]
    c.execute("SELECT MIN(ts), MAX(ts) FROM scada_data")
    min_ts, max_ts = c.fetchone()
    
    conn.close()
    
    print(f"\n完成!")
    print(f"总记录数: {final_count}")
    print(f"时间范围: {min_ts} ~ {max_ts}")
    print(f"新增记录: {total_inserted}")

if __name__ == "__main__":
    generate_extended_mock_data()
