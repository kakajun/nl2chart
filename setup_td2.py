import requests

URL = "http://10.204.252.13:6041/rest/sql"
HEADERS = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ==", "Content-Type": "text/plain"}

def sql(db, query):
    r = requests.post(f"{URL}/{db}", headers=HEADERS, data=query, timeout=30)
    return r.json()

# 清理
print("清理旧库...")
print(sql("", "DROP DATABASE IF EXISTS station_data2"))
print(sql("", "CREATE DATABASE IF NOT EXISTS station_data2"))

# 30 个核心字段的超级表
fields = [
    "ts TIMESTAMP",
    "`a` DOUBLE", "`b` DOUBLE", "`c` DOUBLE", "`d` DOUBLE", "`e` DOUBLE",  # 环境
    "`f` DOUBLE", "`g` DOUBLE", "`h` DOUBLE", "`i` DOUBLE", "`j` DOUBLE",  # 功率/发电量
    "`k` DOUBLE", "`l` DOUBLE", "`m` DOUBLE", "`n` DOUBLE", "`o` DOUBLE",  # 电压/电流/功率
    "`p` DOUBLE", "`q` DOUBLE", "`r` DOUBLE", "`s` DOUBLE", "`t` DOUBLE",  # 频率/功率因数
    "`u` DOUBLE", "`v` DOUBLE", "`w` DOUBLE", "`x` DOUBLE", "`y` DOUBLE",  # 温度/直流
    "`z` DOUBLE", "`aa` DOUBLE", "`ab` DOUBLE", "`ac` DOUBLE", "`ad` DOUBLE",  # 扩展
    "`ae` DOUBLE", "`af` DOUBLE", "`ag` DOUBLE", "`ah` DOUBLE", "`ai` DOUBLE",  # 预留
    "cold VARCHAR(255)", "bit VARCHAR(255)", "other VARCHAR(255)"
]

field_def = ", ".join(fields)
sql_str = f"CREATE STABLE IF NOT EXISTS stable_es_station_pjygcdz_equ ({field_def}) TAGS (equ_code VARCHAR(255), station_code VARCHAR(255))"
print(f"\n创建超级表（{len(fields)} 字段）...")
print(sql("station_data2", sql_str))

# 子表
EQUIPS = ["HBZ_HJ01", "HBZ_F1", "HBZ_F2", "HBZ_F3"]
print("\n创建子表...")
for equ in EQUIPS:
    r = sql("station_data2", f"CREATE TABLE IF NOT EXISTS `{equ}` USING stable_es_station_pjygcdz_equ TAGS ('{equ}', 'hbz')")
    print(f"  {equ}: {r.get('code', 0) == 0 and 'OK' or r}")

# 验证
print("\n验证 INSERT...")
r = sql("station_data2", "INSERT INTO HBZ_HJ01 (ts, a, e, h) VALUES ('2026-05-21 22:00:00', 300.5, 25.0, 1000.0)")
print(f"INSERT: {r}")
r = sql("station_data2", "SELECT COUNT(*) FROM stable_es_station_pjygcdz_equ")
print(f"COUNT: {r}")

print("\n✅ 建表完成")
