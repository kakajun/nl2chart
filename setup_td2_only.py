import requests

TD_URL = "http://10.204.252.13:6041/rest/sql/station_data2"
HEADERS = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ==", "Content-Type": "text/plain"}

def exec_sql(sql):
    resp = requests.post(TD_URL, headers=HEADERS, data=sql, timeout=15)
    return resp.json()

# 重建超级表
print("DROP...")
print(exec_sql("DROP STABLE IF EXISTS stable_es_station_pjygcdz_equ"))

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

print("CREATE STABLE...")
print(exec_sql(f"CREATE STABLE stable_es_station_pjygcdz_equ ({fd}) TAGS (equ_code VARCHAR(255), station_code VARCHAR(255))"))

print("CREATE TABLES...")
for equ in ["HBZ_HJ01", "HBZ_F1", "HBZ_F2", "HBZ_F3"]:
    r = exec_sql(f"CREATE TABLE `{equ}` USING stable_es_station_pjygcdz_equ TAGS ('{equ}', 'hbz')")
    print(f"  {equ}: {r.get('code', 0) == 0 and 'OK' or r}")

print("\nVERIFY INSERT...")
print(exec_sql("INSERT INTO HBZ_HJ01 (ts, a, e, h) VALUES ('2026-05-21 22:00:00', 300.5, 25.0, 1000.0)"))
print(exec_sql("SELECT COUNT(*) FROM stable_es_station_pjygcdz_equ"))
