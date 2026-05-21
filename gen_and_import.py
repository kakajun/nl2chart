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

# 生成 30 天数据（4月22日 - 5月21日），每30分钟一个点
def gen_data():
    equips = ["HBZ_HJ01", "HBZ_F1", "HBZ_F2", "HBZ_F3"]
    base_ts = datetime(2026, 4, 22)
    days = 30
    points_per_day = 48  # 30分钟间隔
    total_points = len(equips) * days * points_per_day
    
    print(f"生成 {days} 天数据: {total_points} 个时间点记录")
    
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
                # 环境监测仪数据
                a = round(random.uniform(200, 900) + random.uniform(-50, 50), 2)  # 辐照度
                b = round(random.uniform(15, 35), 1)  # 环境温度
                c = round(random.uniform(0, 100), 1)  # 湿度
                d = round(random.uniform(0, 360), 1)  # 风向
                e = round(random.uniform(2, 15), 2)  # 风速
                
                # 逆变器/箱变数据
                f = round(random.uniform(0, 500), 2)  # 总有功功率
                g = round(random.uniform(0, 1000), 2)  # 日发电量
                h = round(random.uniform(220, 240), 1)  # A相电压
                i = round(random.uniform(220, 240), 1)  # B相电压
                j = round(random.uniform(220, 240), 1)  # C相电压
                
                cols = ["ts", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
                vals = [f"'{ts_str}'", str(a), str(b), str(c), str(d), str(e),
                        str(f), str(g), str(h), str(i), str(j)]
                
                batch.append(f"INSERT INTO `{equ}` ({', '.join(cols)}) VALUES ({', '.join(vals)})")
                
                if len(batch) >= 20:
                    multi_sql = "; ".join(batch)
                    r = exec_sql(multi_sql)
                    if r.get("code", 0) != 0:
                        print(f"❌ 失败 ({written}): {r.get('desc', r)[:200]}")
                        return written
                    written += len(batch)
                    
                    now = time.time()
                    if now - last_report > 10:
                        rate = written / (now - start)
                        pct = written / total_points * 100
                        print(f"  [{int(now-start)}s] {written}/{total_points} ({pct:.1f}%) {rate:.1f}条/s")
                        last_report = now
                    
                    batch = []
    
    # 最后一批
    if batch:
        multi_sql = "; ".join(batch)
        r = exec_sql(multi_sql)
        if r.get("code", 0) == 0:
            written += len(batch)
        else:
            print(f"❌ 最后一批失败: {r.get('desc', r)[:200]}")
    
    elapsed = time.time() - start
    print(f"\n✅ 完成，共写入 {written}/{total_points} 条，耗时 {int(elapsed)}s")
    return written

# 执行
written = gen_data()

# 验证
r = exec_sql("SELECT COUNT(*) FROM scada_equ")
print(f"超级表总记录数: {r.get('data', [[0]])[0][0]}")
for equ in ["HBZ_HJ01", "HBZ_F1", "HBZ_F2", "HBZ_F3"]:
    r = exec_sql(f"SELECT COUNT(*) FROM {equ}")
    print(f"  {equ}: {r.get('data', [[0]])[0][0]} 行")

# 查看最新数据
r = exec_sql("SELECT ts, a, b, e FROM HBZ_HJ01 ORDER BY ts DESC LIMIT 3")
print(f"\n最新3条 HJ01:")
for row in r.get('data', []):
    print(f"  {row}")
