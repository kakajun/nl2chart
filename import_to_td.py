import sqlite3
import requests
from collections import defaultdict, Counter

DB_PATH = "/root/.openclaw/workspace/nl2chart/backend/app/db/mock_scada.db"
TD_URL = "http://10.204.252.13:6041/rest/sql/station_data"
HEADERS = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ==", "Content-Type": "text/plain"}

KEY_FIELDS = set(["a","b","c","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w"])

def exec_sql(sql):
    resp = requests.post(TD_URL, headers=HEADERS, data=sql, timeout=30)
    return resp.json()

# 读取数据
sq_conn = sqlite3.connect(DB_PATH)
sq_cursor = sq_conn.cursor()
sq_cursor.execute("SELECT ts, equ_code, point_code, value FROM scada_data ORDER BY ts DESC, equ_code")
rows = sq_cursor.fetchall()
sq_conn.close()

# 聚合 + 筛选每设备最新30条
grouped_all = defaultdict(dict)
for ts, equ_code, pcode, val in rows:
    if pcode in KEY_FIELDS:
        grouped_all[(ts, equ_code)][pcode] = val

device_counts = Counter()
grouped = {}
for key in grouped_all.keys():
    ts, equ_code = key
    if device_counts[equ_code] < 30:
        grouped[key] = grouped_all[key]
        device_counts[equ_code] += 1

print(f"筛选后 {len(grouped)} 行（每设备最新30条）")

# 批量写入，每批10条
batch = []
written = 0
for (ts, equ_code), points in grouped.items():
    cols = ["ts"] + [f"`{p}`" for p in sorted(points.keys())]
    vals = [f"'{ts}'"] + [str(v) if v is not None else "NULL" for v in [points[p] for p in sorted(points.keys())]]
    batch.append(f"INSERT INTO `{equ_code}` ({', '.join(cols)}) VALUES ({', '.join(vals)})")
    
    if len(batch) >= 10:
        multi_sql = "; ".join(batch)
        r = exec_sql(multi_sql)
        if r.get("code", 0) != 0:
            print(f"❌ 失败: {r.get('desc', r)}")
            break
        written += len(batch)
        print(f"  已写入 {written} / {len(grouped)} 行...")
        batch = []

if batch:
    multi_sql = "; ".join(batch)
    r = exec_sql(multi_sql)
    if r.get("code", 0) == 0:
        written += len(batch)
    else:
        print(f"❌ 最后一批失败: {r.get('desc', r)}")

print(f"\n✅ 完成，共写入 {written} 行")

# 验证
r = exec_sql("SELECT COUNT(*) FROM stable_es_station_pjygcdz_equ")
print(f"超级表总记录数: {r}")
