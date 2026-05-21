import requests
import random
from datetime import datetime, timedelta
import time

TD_URL = "http://10.204.252.13:6041/rest/sql/station_data2"
HEADERS = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ==", "Content-Type": "text/plain"}

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

# 参数
equips = ["HBZ_HJ01", "HBZ_F1", "HBZ_F2", "HBZ_F3"]
base_ts = datetime(2026, 4, 22)
days = 30
points_per_day = 48  # 30分钟间隔
BATCH = 10

total_points = len(equips) * days * points_per_day
print(f"生成 {days} 天数据，{len(equips)} 台设备，共 {total_points} 条记录，batch={BATCH}")

batch = []
written = 0
start = time.time()
last_report = start

for d in range(days):
    day = base_ts + timedelta(days=d)
    for p in range(points_per_day):
        ts = day + timedelta(minutes=p * 30)
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        
        for equ in equips:
            a = round(random.uniform(200, 900), 2)
            b = round(random.uniform(15, 35), 1)
            c = round(random.uniform(0, 100), 1)
            d = round(random.uniform(0, 360), 1)
            e = round(random.uniform(2, 15), 2)
            f = round(random.uniform(0, 500), 2)
            g = round(random.uniform(0, 1000), 2)
            h = round(random.uniform(220, 240), 1)
            i = round(random.uniform(220, 240), 1)
            j = round(random.uniform(220, 240), 1)
            
            cols = "ts, a, b, c, d, e, f, g, h, i, j"
            vals = f"'{ts_str}', {a}, {b}, {c}, {d}, {e}, {f}, {g}, {h}, {i}, {j}"
            batch.append(f"INSERT INTO `{equ}` ({cols}) VALUES ({vals})")
            
            if len(batch) >= BATCH:
                multi_sql = "; ".join(batch)
                r = exec_sql(multi_sql)
                if r.get("code", 0) != 0:
                    print(f"\n❌ 失败 ({written}): {r.get('desc', r)[:200]}")
                    print(f"SQL preview: {multi_sql[:200]}...")
                    break
                written += len(batch)
                
                now = time.time()
                if now - last_report > 5:
                    rate = written / (now - start)
                    pct = written / total_points * 100
                    print(f"  [{int(now-start):3d}s] {written:5d}/{total_points} ({pct:5.1f}%) {rate:6.1f}条/s")
                    last_report = now
                
                batch = []

# 最后一批
if batch:
    multi_sql = "; ".join(batch)
    r = exec_sql(multi_sql)
    if r.get("code", 0) == 0:
        written += len(batch)
    else:
        print(f"\n❌ 最后一批失败: {r.get('desc', r)[:200]}")

elapsed = time.time() - start
print(f"\n✅ 完成，{written}/{total_points} 条，耗时 {int(elapsed)}s")

# 验证
r = exec_sql("SELECT COUNT(*) FROM scada_equ")
count = r.get('data', [[0]])[0][0]
print(f"超级表总记录数: {count}")
for equ in equips:
    r = exec_sql(f"SELECT COUNT(*) FROM {equ}")
    c = r.get('data', [[0]])[0][0]
    print(f"  {equ}: {c} 行")

r = exec_sql("SELECT ts, a, b, e FROM HBZ_HJ01 ORDER BY ts DESC LIMIT 3")
print(f"\n最新3条 HJ01:")
for row in r.get('data', []):
    print(f"  {row}")
