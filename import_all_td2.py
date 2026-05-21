import sqlite3
import requests
from collections import defaultdict
import time

TD_URL = "http://10.204.252.13:6041/rest/sql/station_data2"
HEADERS = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ==", "Content-Type": "text/plain"}
DB_PATH = "/root/.openclaw/workspace/nl2chart/backend/app/db/mock_scada.db"

def exec_sql(sql):
    resp = requests.post(TD_URL, headers=HEADERS, data=sql, timeout=60)
    return resp.json()

# ========== 1. 重建超级表（无 bit 关键字） ==========
print("重建超级表...")
exec_sql("DROP STABLE IF EXISTS stable_es_station_pjygcdz_equ")

fields = [
    "ts TIMESTAMP",
    "`a` DOUBLE", "`b` DOUBLE", "`c` DOUBLE", "`d` DOUBLE", "`e` DOUBLE",
    "`f` DOUBLE", "`g` DOUBLE", "`h` DOUBLE", "`i` DOUBLE", "`j` DOUBLE",
    "`k` DOUBLE", "`l` DOUBLE", "`m` DOUBLE", "`n` DOUBLE", "`o` DOUBLE",
    "`p` DOUBLE", "`q` DOUBLE", "`r` DOUBLE", "`s` DOUBLE", "`t` DOUBLE",
    "`u` DOUBLE", "`v` DOUBLE", "`w` DOUBLE", "`x` DOUBLE", "`y` DOUBLE",
    "`z` DOUBLE", "`aa` DOUBLE", "`ab` DOUBLE", "`ac` DOUBLE", "`ad` DOUBLE",
    "`ae` DOUBLE", "`af` DOUBLE", "`ag` DOUBLE", "`ah` DOUBLE", "`ai` DOUBLE",
    "cold VARCHAR(255)", "bitfield VARCHAR(255)", "other VARCHAR(255)"
]
fd = ", ".join(fields)
r = exec_sql(f"CREATE STABLE stable_es_station_pjygcdz_equ ({fd}) TAGS (equ_code VARCHAR(255), station_code VARCHAR(255))")
print(f"  CREATE STABLE: {r.get('code', 0) == 0 and 'OK' or r}")

EQUIPS = ["HBZ_HJ01", "HBZ_F1", "HBZ_F2", "HBZ_F3"]
for equ in EQUIPS:
    r = exec_sql(f"CREATE TABLE `{equ}` USING stable_es_station_pjygcdz_equ TAGS ('{equ}', 'hbz')")
    print(f"  CREATE {equ}: {r.get('code', 0) == 0 and 'OK' or r}")

# ========== 2. 读取 SQLite 数据 ==========
sq_conn = sqlite3.connect(DB_PATH)
sq_cursor = sq_conn.cursor()
sq_cursor.execute("SELECT ts, equ_code, point_code, value FROM scada_data ORDER BY ts, equ_code")
rows = sq_cursor.fetchall()
sq_conn.close()
print(f"\n共 {len(rows)} 条原始记录")

# ========== 3. 聚合 + 过滤字段 ==========
valid_cols = set([f.split()[0].strip("`'") for f in fields[1:]])  # 去掉 ts
valid_cols.discard("VARCHAR")  # 清理残留
grouped = defaultdict(dict)
for ts, equ_code, pcode, val in rows:
    if pcode in valid_cols:
        grouped[(ts, equ_code)][pcode] = val
print(f"聚合为 {len(grouped)} 行（{len(valid_cols)} 字段）")

# ========== 4. 分批写入 ==========
batch = []
written = 0
total = len(grouped)
start = time.time()

for (ts, equ_code), points in grouped.items():
    cols = ["ts"] + [f"`{p}`" for p in sorted(points.keys())]
    vals = [f"'{ts}'"] + [str(v) if v is not None else "NULL" for v in [points[p] for p in sorted(points.keys())]]
    batch.append(f"INSERT INTO `{equ_code}` ({', '.join(cols)}) VALUES ({', '.join(vals)})")
    
    if len(batch) >= 10:
        multi_sql = "; ".join(batch)
        r = exec_sql(multi_sql)
        if r.get("code", 0) != 0:
            print(f"❌ 失败 ({written}/{total}): {r.get('desc', r)[:200]}")
            break
        written += len(batch)
        if written % 200 == 0:
            elapsed = time.time() - start
            rate = written / elapsed if elapsed > 0 else 0
            print(f"  [{int(elapsed)}s] {written}/{total} ({rate:.1f}/s)")
        batch = []

if batch:
    multi_sql = "; ".join(batch)
    r = exec_sql(multi_sql)
    if r.get("code", 0) == 0:
        written += len(batch)
    else:
        print(f"❌ 最后一批失败: {r.get('desc', r)[:200]}")

elapsed = time.time() - start
print(f"\n✅ 完成，共写入 {written}/{total} 行，耗时 {int(elapsed)}s")

# ========== 5. 验证 ==========
r = exec_sql("SELECT COUNT(*) FROM stable_es_station_pjygcdz_equ")
print(f"超级表总记录数: {r.get('data', [[0]])[0][0]}")
for equ in EQUIPS:
    r = exec_sql(f"SELECT COUNT(*) FROM {equ}")
    print(f"  {equ}: {r.get('data', [[0]])[0][0]} 行")
