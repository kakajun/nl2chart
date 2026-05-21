import requests
import string

BASE_URL = "http://10.204.252.13:6041/rest/sql/station_data"
HEADERS = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ==", "Content-Type": "text/plain"}

def exec_sql(sql):
    resp = requests.post(BASE_URL, headers=HEADERS, data=sql, timeout=60)
    return resp.json()

# 1. 删除旧超级表（级联删除子表）
print("删除旧超级表...")
r = exec_sql("DROP STABLE IF EXISTS stable_es_station_pjygcdz_equ")
print(r)

# 2. 生成所有测点字段
fields = ["ts TIMESTAMP"]
letters = list(string.ascii_lowercase)

# a-z
for c in letters:
    fields.append(f"`{c}` DOUBLE")

# aa-zz (但只到 zh，因为 mock 数据最大到 zh)
for c1 in letters:
    for c2 in letters:
        col = f"{c1}{c2}"
        if col > "zh":  # mock 数据最大到 zh
            break
        fields.append(f"`{col}` DOUBLE")

fields.append("cold VARCHAR(255)")
fields.append("bit VARCHAR(255)")
fields.append("other VARCHAR(255)")

print(f"总字段数: {len(fields)}")

# 3. 分批添加字段 — 先创建超级表带核心字段，再用 ALTER 添加其余字段
# TDengine REST API 可能限制单条 SQL 长度，先创建基础表
base_fields = fields[:100]  # 先放 100 个字段
remain_fields = fields[100:]

field_def = ", ".join(base_fields)
sql = f"CREATE STABLE IF NOT EXISTS stable_es_station_pjygcdz_equ ({field_def}) TAGS (equ_code VARCHAR(255), station_code VARCHAR(255))"
print("创建基础超级表...")
r = exec_sql(sql)
print(r)

# 4. 分批 ALTER 添加剩余字段
batch_size = 50
for i in range(0, len(remain_fields), batch_size):
    batch = remain_fields[i:i+batch_size]
    alter_sql = "ALTER STABLE stable_es_station_pjygcdz_equ " + ", ".join([f"ADD COLUMN {f}" for f in batch])
    print(f"添加字段 {i+1}~{i+len(batch)}...")
    r = exec_sql(alter_sql)
    if r.get("code", 0) != 0:
        print(f"  ❌ 失败: {r}")
        break
    else:
        print(f"  ✅ OK")

# 5. 创建子表
EQUIPS = ["HBZ_HJ01", "HBZ_F1", "HBZ_F2", "HBZ_F3"]
print("\n创建子表...")
for equ_code in EQUIPS:
    sql = f"CREATE TABLE IF NOT EXISTS `{equ_code}` USING stable_es_station_pjygcdz_equ TAGS ('{equ_code}', 'hbz')"
    r = exec_sql(sql)
    print(f"  {equ_code}: {r.get('code', 0) == 0 and 'OK' or r}")

print("\n✅ 超级表重建完成")
