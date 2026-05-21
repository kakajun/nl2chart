import requests

TD_URL = "http://10.204.252.13:6041/rest/sql"
HEADERS = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ==", "Content-Type": "text/plain"}

def exec_sql(sql):
    resp = requests.post(TD_URL, headers=HEADERS, data=sql, timeout=15)
    return resp.json()

print("清理重建库...")
print(exec_sql("DROP DATABASE IF EXISTS station_data2"))
print(exec_sql("CREATE DATABASE IF NOT EXISTS station_data2"))

TD_URL = "http://10.204.252.13:6041/rest/sql/station_data2"

def exec_sql2(sql):
    resp = requests.post(TD_URL, headers=HEADERS, data=sql, timeout=15)
    return resp.json()

print("\n重建超级表...")
exec_sql2("DROP STABLE IF EXISTS scada_equ")

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
r = exec_sql2(f"CREATE STABLE scada_equ ({fd}) TAGS (equ_code VARCHAR(255), station_code VARCHAR(255))")
print(f"  CREATE: {r.get('code', 0) == 0 and 'OK' or r}")

for equ in ["HBZ_HJ01", "HBZ_F1", "HBZ_F2", "HBZ_F3"]:
    r = exec_sql2(f"CREATE TABLE `{equ}` USING scada_equ TAGS ('{equ}', 'hbz')")
    print(f"  {equ}: {r.get('code', 0) == 0 and 'OK' or r}")

r = exec_sql2("INSERT INTO HBZ_HJ01 (ts, a, e, h) VALUES ('2026-05-21 22:00:00', 300.5, 25.0, 1000.0)")
print(f"  测试 INSERT: {r.get('code', 0) == 0 and 'OK' or r}")

r = exec_sql2("SELECT COUNT(*) FROM scada_equ")
print(f"  COUNT: {r}")
print("\n✅ 建表完成")
