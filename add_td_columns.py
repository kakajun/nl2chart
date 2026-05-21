import requests
import string
import time

BASE_URL = "http://10.204.252.13:6041/rest/sql/station_data"
HEADERS = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ==", "Content-Type": "text/plain"}

def exec_sql(sql):
    resp = requests.post(BASE_URL, headers=HEADERS, data=sql, timeout=30)
    return resp.json()

# 生成所有测点字段
fields = []
letters = list(string.ascii_lowercase)

# a-z
for c in letters:
    fields.append(f"`{c}` DOUBLE")

# aa-zz (到 zh)
for c1 in letters:
    for c2 in letters:
        col = f"{c1}{c2}"
        if col > "zh":
            break
        fields.append(f"`{col}` DOUBLE")

fields.append("cold VARCHAR(255)")
fields.append("bit VARCHAR(255)")
fields.append("other VARCHAR(255)")

print(f"总字段数: {len(fields)}")

# 获取当前超级表已有字段数
r = exec_sql("DESCRIBE stable_es_station_pjygcdz_equ")
if r.get("code", 0) == 0:
    existing = len(r.get("data", []))
    print(f"当前已有字段数: {existing}")
else:
    existing = 0

# 计算还需要添加的字段
# 基础表已包含 ts + 前99个字段 + tags，实际需要添加剩余字段
# 我们直接计算需要添加哪些
# 为了简单，获取当前所有列名，然后补缺失的

existing_cols = set()
if r.get("code", 0) == 0:
    for row in r.get("data", []):
        existing_cols.add(row[0])

needed = [f for f in fields if f.split()[0].strip('`') not in existing_cols and f.split()[0] not in existing_cols]
print(f"需要添加字段数: {len(needed)}")

# 逐个 ALTER 添加
added = 0
for f in needed:
    col_name = f.split()[0]
    alter_sql = f"ALTER STABLE stable_es_station_pjygcdz_equ ADD COLUMN {f}"
    r = exec_sql(alter_sql)
    if r.get("code", 0) != 0:
        print(f"❌ 添加 {col_name} 失败: {r.get('desc', r)}")
        break
    added += 1
    if added % 50 == 0:
        print(f"  已添加 {added} 个字段...")
    time.sleep(0.05)  # 避免请求过快

print(f"\n✅ 共添加 {added} 个字段")

# 验证最终字段数
r = exec_sql("DESCRIBE stable_es_station_pjygcdz_equ")
if r.get("code", 0) == 0:
    print(f"最终字段数: {len(r.get('data', []))}")
