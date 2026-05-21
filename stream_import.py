import sqlite3
import requests
from collections import defaultdict
import time

TD_URL = "http://10.204.252.13:6041/rest/sql/station_data2"
HEADERS = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ==", "Content-Type": "text/plain"}
DB_PATH = "/root/.openclaw/workspace/nl2chart/backend/app/db/mock_scada.db"

VALID_COLS = set("abcdefghijklmnopqrstuvwxyz" + "".join([f"a{c}" for c in "abcdefghijklmnopqrstuvwxyz"]))
VALID_COLS = set(list("abcdefghijklmnopqrstuvwxyz") + [f"a{c}" for c in "abcdefghijklmnopqrstuvwxyz"])
VALID_COLS = set(["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","aa","ab","ac","ad","ae","af","ag","ah","ai"])

EQUIPS = {"HBZ_HJ01", "HBZ_F1", "HBZ_F2", "HBZ_F3"}

def exec_sql(sql):
    for attempt in range(3):
        try:
            resp = requests.post(TD_URL, headers=HEADERS, data=sql, timeout=30)
            return resp.json()
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                return {"code": -1, "desc": str(e)[:200]}

# 流式读取 + 批量写入
sq_conn = sqlite3.connect(DB_PATH)
sq_cursor = sq_conn.cursor()
sq_cursor.execute("SELECT ts, equ_code, point_code, value FROM scada_data ORDER BY ts, equ_code")

grouped = defaultdict(dict)
written = 0
total_ts = 0
batch = []
start = time.time()
last_report = start
BATCH_SIZE = 5

for row in sq_cursor:
    ts, equ_code, pcode, val = row
    if equ_code not in EQUIPS or pcode not in VALID_COLS:
        continue
    
    key = (ts, equ_code)
    grouped[key][pcode] = val
    
    # 当 key 变化时，前一个 key 的数据已经完整
    # 但因为 ORDER BY ts, equ_code，同一 (ts, equ_code) 的记录是连续的
    # 我们用一个 trick：当内存中的 grouped 达到一定大小时写入
    if len(grouped) >= BATCH_SIZE:  # 每 20 个时间点写一次
        for (ts2, equ2), points in grouped.items():
            cols = ["ts"] + [f"`{p}`" for p in sorted(points.keys())]
            vals = [f"'{ts2}'"] + [str(v) if v is not None else "NULL" for v in [points[p] for p in sorted(points.keys())]]
            batch.append(f"INSERT INTO `{equ2}` ({', '.join(cols)}) VALUES ({', '.join(vals)})")
        
        # 写入 TDengine
        multi_sql = "; ".join(batch)
        r = exec_sql(multi_sql)
        if r.get("code", 0) != 0:
            print(f"❌ 失败 ({written}): {r.get('desc', r)[:200]}")
            break
        
        written += len(batch)
        total_ts += len(grouped)
        
        now = time.time()
        if now - last_report > 5:
            rate = written / (now - start) if now > start else 0
            print(f"  [{int(now-start)}s] {total_ts} 时间点写入，{rate:.1f} 条/s")
            last_report = now
        
        grouped.clear()
        batch = []

# 处理剩余数据
if grouped:
    for (ts2, equ2), points in grouped.items():
        cols = ["ts"] + [f"`{p}`" for p in sorted(points.keys())]
        vals = [f"'{ts2}'"] + [str(v) if v is not None else "NULL" for v in [points[p] for p in sorted(points.keys())]]
        batch.append(f"INSERT INTO `{equ2}` ({', '.join(cols)}) VALUES ({', '.join(vals)})")
    
    multi_sql = "; ".join(batch)
    r = exec_sql(multi_sql)
    if r.get("code", 0) == 0:
        written += len(batch)
        total_ts += len(grouped)
    else:
        print(f"❌ 最后一批失败: {r.get('desc', r)[:200]}")

sq_conn.close()

elapsed = time.time() - start
print(f"\n✅ 完成，{total_ts} 个时间点，{written} 条 INSERT，耗时 {int(elapsed)}s")

# 验证
r = exec_sql("SELECT COUNT(*) FROM scada_equ")
print(f"超级表总记录数: {r.get('data', [[0]])[0][0]}")
for equ in sorted(EQUIPS):
    r = exec_sql(f"SELECT COUNT(*) FROM {equ}")
    print(f"  {equ}: {r.get('data', [[0]])[0][0]} 行")
