import requests

BASE_URL = "http://10.204.252.13:6041/rest/sql/station_data"
HEADERS = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ==", "Content-Type": "text/plain"}

def exec_sql(sql: str) -> dict:
    resp = requests.post(BASE_URL, headers=HEADERS, data=sql, timeout=30)
    return resp.json()

# 1. 创建数据库
print("创建数据库 station_data...")
r = exec_sql("CREATE DATABASE IF NOT EXISTS station_data")
print(r)

# 2. 生成超级表字段定义 — 所有已知测点字段用反引号包裹
fields = ["ts TIMESTAMP"]

# a-z
import string
letters = list(string.ascii_lowercase)
for c in letters:
    fields.append(f"`{c}` DOUBLE")

# aa-dv
for c1 in letters:
    for c2 in letters:
        col = f"{c1}{c2}"
        if col > "dv":
            break
        fields.append(f"`{col}` DOUBLE")
    if c1 == "d":
        break

fields.append("cold VARCHAR(255)")
fields.append("bit VARCHAR(255)")
fields.append("other VARCHAR(255)")

field_def = ", ".join(fields)

# 3. 创建超级表
sql = f"CREATE STABLE IF NOT EXISTS stable_es_station_pjygcdz_equ ({field_def}) TAGS (equ_code VARCHAR(255), station_code VARCHAR(255))"
print(f"\n创建超级表，字段数: {len(fields)}...")
r = exec_sql(sql)
print(r)

# 4. 创建子表
EQUIPS = [
    ("HBZ_HJ01", "hbz"),
    ("HBZ_F1", "hbz"),
    ("HBZ_F2", "hbz"),
    ("HBZ_F3", "hbz"),
]

print("\n创建子表...")
for equ_code, station_code in EQUIPS:
    sql = f"CREATE TABLE IF NOT EXISTS `{equ_code}` USING stable_es_station_pjygcdz_equ TAGS ('{equ_code}', '{station_code}')"
    r = exec_sql(sql)
    print(f"  {equ_code}: {r.get('code', 0) == 0 and 'OK' or r}")

print("\n✅ 库表创建完成")
