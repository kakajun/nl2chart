import requests

TD_URL = "http://10.204.252.13:6041/rest/sql"
HEADERS = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ==", "Content-Type": "text/plain"}

def exec_sql(sql):
    resp = requests.post(TD_URL, headers=HEADERS, data=sql, timeout=30)
    return resp.json()

# 1. 删除旧库
print("删除旧库...")
r = exec_sql("DROP DATABASE IF EXISTS station_data")
print(r)

# 2. 创建新库
print("\n创建新库...")
r = exec_sql("CREATE DATABASE IF NOT EXISTS station_data")
print(r)

# 3. 只创建核心字段的超级表
fields = [
    "ts TIMESTAMP",
    "`a` DOUBLE", "`b` DOUBLE", "`c` DOUBLE", "`d` DOUBLE",
    "`e` DOUBLE", "`f` DOUBLE", "`g` DOUBLE", "`h` DOUBLE",
    "`i` DOUBLE", "`j` DOUBLE", "`k` DOUBLE", "`l` DOUBLE",
    "`m` DOUBLE", "`n` DOUBLE", "`o` DOUBLE", "`p` DOUBLE",
    "`q` DOUBLE", "`r` DOUBLE", "`s` DOUBLE", "`t` DOUBLE",
    "`u` DOUBLE", "`v` DOUBLE", "`w` DOUBLE", "`x` DOUBLE",
    "`y` DOUBLE", "`z` DOUBLE",
    "`aa` DOUBLE", "`ab` DOUBLE", "`ac` DOUBLE", "`ad` DOUBLE",
    "`ae` DOUBLE", "`af` DOUBLE", "`ag` DOUBLE", "`ah` DOUBLE",
    "`ai` DOUBLE", "`aj` DOUBLE", "`ak` DOUBLE", "`al` DOUBLE",
    "`am` DOUBLE", "`an` DOUBLE", "`ao` DOUBLE", "`ap` DOUBLE",
    "`aq` DOUBLE", "`ar` DOUBLE", "`as` DOUBLE", "`at` DOUBLE",
    "`au` DOUBLE", "`av` DOUBLE", "`aw` DOUBLE", "`ax` DOUBLE",
    "`ay` DOUBLE", "`az` DOUBLE",
    "`ba` DOUBLE", "`bb` DOUBLE", "`bc` DOUBLE", "`bd` DOUBLE",
    "`be` DOUBLE", "`bf` DOUBLE", "`bg` DOUBLE", "`bh` DOUBLE",
    "`bi` DOUBLE", "`bj` DOUBLE", "`bk` DOUBLE", "`bl` DOUBLE",
    "`bm` DOUBLE", "`bn` DOUBLE", "`bo` DOUBLE", "`bp` DOUBLE",
    "`bq` DOUBLE", "`br` DOUBLE", "`bs` DOUBLE", "`bt` DOUBLE",
    "`bu` DOUBLE", "`bv` DOUBLE", "`bw` DOUBLE", "`bx` DOUBLE",
    "`by` DOUBLE", "`bz` DOUBLE",
    "cold VARCHAR(255)", "bit VARCHAR(255)", "other VARCHAR(255)"
]

field_def = ", ".join(fields)
sql = f"CREATE STABLE IF NOT EXISTS station_data.stable_es_station_pjygcdz_equ ({field_def}) TAGS (equ_code VARCHAR(255), station_code VARCHAR(255))"
print(f"\n创建超级表（{len(fields)} 字段）...")
r = exec_sql(sql)
print(r)

# 4. 创建子表
EQUIPS = ["HBZ_HJ01", "HBZ_F1", "HBZ_F2", "HBZ_F3"]
print("\n创建子表...")
for equ_code in EQUIPS:
    sql = f"CREATE TABLE IF NOT EXISTS station_data.`{equ_code}` USING station_data.stable_es_station_pjygcdz_equ TAGS ('{equ_code}', 'hbz')"
    r = exec_sql(sql)
    print(f"  {equ_code}: {r.get('code', 0) == 0 and 'OK' or r}")

# 5. 验证
print("\n验证...")
r = exec_sql("USE station_data; SHOW TABLES")
print(f"表列表: {[row[0] for row in r.get('data', [])]}")
r = exec_sql("USE station_data; SELECT COUNT(*) FROM stable_es_station_pjygcdz_equ")
print(f"超级表记录数: {r}")

print("\n✅ 重建完成")
