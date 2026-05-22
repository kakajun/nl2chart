import sqlite3
import taosws
from pathlib import Path
from collections import defaultdict

# 配置
SQLITE_DB = Path(__file__).parent / "mock_scada.db"
TD_HOST = "10.204.252.13"
TD_PORT = "6041"
TD_DB = "station_data"

# 超级表名
SUPER_TABLE = "stable_es_station_pjygcdz_equ"


def connect_tdengine():
    conn_str = f"taosws://{TD_HOST}:{TD_PORT}/{TD_DB}"
    return taosws.connect(conn_str)


def get_table_schema(conn):
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {SUPER_TABLE}")
    cols = cursor.fetchall()
    point_cols = []
    for col in cols:
        name = col[0]
        note = col[3] if len(col) > 3 else ""
        if name == "ts" or note == "TAG":
            continue
        point_cols.append(name)
    cursor.close()
    return point_cols


def load_mock_data(db_path, station="HBZ"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("SELECT DISTINCT ts FROM scada_data WHERE station_code = ? ORDER BY ts", (station,))
    timestamps = [r[0] for r in c.fetchall()]
    print(f"[Import] 时间戳数量: {len(timestamps)}")
    
    c.execute("SELECT DISTINCT point_code FROM scada_data WHERE station_code = ? ORDER BY point_code", (station,))
    point_codes = [r[0] for r in c.fetchall()]
    print(f"[Import] 测点数量: {len(point_codes)}")
    
    device_data = defaultdict(lambda: defaultdict(dict))
    c.execute("SELECT ts, equ_code, point_code, value FROM scada_data WHERE station_code = ? ORDER BY ts, equ_code, point_code", (station,))
    
    batch_size = 50000
    count = 0
    while True:
        rows = c.fetchmany(batch_size)
        if not rows:
            break
        for ts, equ_code, pcode, val in rows:
            device_data[equ_code][ts][pcode] = val
            count += 1
        if count % 500000 == 0:
            print(f"[Import] 已加载 {count} 条...")
    
    conn.close()
    print(f"[Import] 总加载: {count} 条, 设备数: {len(device_data)}")
    return timestamps, point_codes, device_data


def import_to_tdengine():
    print("=" * 60)
    print("Mock 数据导入 TDengine")
    print("=" * 60)
    
    td_conn = connect_tdengine()
    cursor = td_conn.cursor()
    print("[Import] TDengine 连接成功")
    
    point_cols = get_table_schema(td_conn)
    print(f"[Import] 超级表 {SUPER_TABLE}")
    print(f"[Import] 测点列: {len(point_cols)} 个")
    
    timestamps, point_codes, device_data = load_mock_data(SQLITE_DB)
    
    valid_codes = [c for c in point_codes if c in point_cols]
    skipped_codes = [c for c in point_codes if c not in point_cols]
    print(f"[Import] 匹配测点: {len(valid_codes)} 个")
    print(f"[Import] 跳过测点: {len(skipped_codes)} 个")
    if skipped_codes:
        print(f"[Import] 前10个跳过: {sorted(skipped_codes)[:10]}")
    
    total_inserted = 0
    for device_name, device_points in device_data.items():
        table_name = device_name
        
        print(f"\n[Import] 导入设备 {table_name}:")
        print(f"  时间点: {len(device_points)}")
        
        try:
            cursor.execute(f"DELETE FROM `{table_name}`")
            td_conn.commit()
            print(f"  已清空旧数据")
        except Exception as e:
            print(f"  清空旧数据失败: {e}")
        
        cols_sql = ",".join(["ts"] + valid_codes)
        
        # 批量多值插入，每批 100 条
        batch_size = 100
        all_ts = sorted(device_points.keys())
        inserted = 0
        
        for batch_start in range(0, len(all_ts), batch_size):
            batch_ts = all_ts[batch_start:batch_start + batch_size]
            values_list = []
            
            for ts in batch_ts:
                row_data = device_points[ts]
                vals = [f"'{ts}'"]
                for code in valid_codes:
                    val = row_data.get(code, None)
                    if val is None:
                        vals.append("NULL")
                    else:
                        vals.append(str(val))
                values_list.append(f"({','.join(vals)})")
            
            sql = f"INSERT INTO `{table_name}` ({cols_sql}) VALUES {','.join(values_list)}"
            
            try:
                cursor.execute(sql)
                td_conn.commit()
                inserted += len(batch_ts)
                if batch_start % 500 == 0 or batch_start + batch_size >= len(all_ts):
                    print(f"  已导入 {inserted}/{len(device_points)}")
            except Exception as e:
                print(f"  插入失败: {e}")
                # 尝试单条插入这批
                for ts in batch_ts:
                    row_data = device_points[ts]
                    vals = [f"'{ts}'"]
                    for code in valid_codes:
                        val = row_data.get(code, None)
                        if val is None:
                            vals.append("NULL")
                        else:
                            vals.append(str(val))
                    sql_single = f"INSERT INTO `{table_name}` ({cols_sql}) VALUES ({','.join(vals)})"
                    try:
                        cursor.execute(sql_single)
                        inserted += 1
                    except Exception as e2:
                        print(f"    单条失败 {ts}: {e2}")
                        break
                td_conn.commit()
        
        total_inserted += inserted
        print(f"  ✅ 导入 {inserted} 条")
        
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        count = cursor.fetchone()[0]
        print(f"  表内总数: {count}")
    
    cursor.close()
    td_conn.close()
    
    print(f"\n[Import] ✅ 全部完成! 总导入: {total_inserted} 条")
    print("=" * 60)


if __name__ == "__main__":
    import_to_tdengine()
