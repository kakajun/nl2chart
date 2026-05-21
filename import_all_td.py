import sqlite3
import taosws
from collections import defaultdict
import time

DB_PATH = "/root/.openclaw/workspace/nl2chart/backend/app/db/mock_scada.db"
HOST = "10.204.252.13"
PORT = 6041
USER = "root"
PASS = "taosdata"
DB = "station_data"

CORE_FIELDS = set(["a","b","c","e","f","h","i","j","k","l","n","o","q","s","u","w"])

conn = taosws.connect(f"taosws://{USER}:{PASS}@{HOST}:{PORT}/{DB}")
cursor = conn.cursor()

sq_conn = sqlite3.connect(DB_PATH)
sq_cursor = sq_conn.cursor()
sq_cursor.execute("SELECT ts, equ_code, point_code, value FROM scada_data ORDER BY ts, equ_code")
rows = sq_cursor.fetchall()
sq_conn.close()

grouped = defaultdict(dict)
for ts, equ_code, pcode, val in rows:
    if pcode in CORE_FIELDS:
        grouped[(ts, equ_code)][pcode] = val

total = len(grouped)
print(f"总任务: {total} 行")

written = 0
start = time.time()
for (ts, equ_code), points in grouped.items():
    cols = ["ts"] + [f"`{p}`" for p in sorted(points.keys())]
    vals = [f"'{ts}'"] + [str(v) if v is not None else "NULL" for v in [points[p] for p in sorted(points.keys())]]
    sql = f"INSERT INTO `{equ_code}` ({', '.join(cols)}) VALUES ({', '.join(vals)})"
    try:
        cursor.execute(sql)
        written += 1
        if written % 100 == 0:
            elapsed = time.time() - start
            rate = written / elapsed if elapsed > 0 else 0
            left = (total - written) / rate if rate > 0 else 0
            log = f"[{int(elapsed)}s] {written}/{total} ({rate:.1f}/s) 剩余约 {int(left)}s"
            print(log)
            with open("/root/.openclaw/workspace/nl2chart/import_progress.log", "a") as f:
                f.write(log + "\n")
    except Exception as e:
        print(f"❌ 失败 @ {written}: {e}")
        with open("/root/.openclaw/workspace/nl2chart/import_progress.log", "a") as f:
            f.write(f"FAIL @ {written}: {e}\n")
        break

print(f"\n✅ 完成 {written}/{total}")
cursor.execute("SELECT COUNT(*) FROM stable_es_station_pjygcdz_equ")
print(f"超级表总记录数: {cursor.fetchall()}")
conn.close()
