import requests

URL = 'http://10.204.252.13:6041/rest/sql/station_data2'
HEADERS = {'Authorization': 'Basic cm9vdDp0YW9zZGF0YQ==', 'Content-Type': 'text/plain'}

# 测试长名字 + 下划线
tests = [
    ('stable_test_123', 'h1'),      # 15字符
    ('stable_es_station', 'hj01'),  # 17字符
    ('stable_es_station_pjygcdz', 'hj01'),  # 25字符
    ('stable_es_station_pjygcdz_e', 'hj01'), # 26字符
]

for stable, child in tests:
    # DROP
    r = requests.post(URL, headers=HEADERS, data=f"DROP STABLE IF EXISTS {stable}", timeout=15)
    
    # CREATE
    r = requests.post(URL, headers=HEADERS, data=f"CREATE STABLE {stable} (ts TIMESTAMP, a DOUBLE) TAGS (equ VARCHAR(50))", timeout=15)
    create_ok = r.json().get('code', -1) == 0
    
    # TABLE
    r = requests.post(URL, headers=HEADERS, data=f"CREATE TABLE {child} USING {stable} TAGS ('{child}')", timeout=15)
    table_ok = r.json().get('code', -1) == 0
    
    # INSERT
    r = requests.post(URL, headers=HEADERS, data=f"INSERT INTO {child} (ts, a) VALUES ('2026-05-21 22:00:00', 1.0)", timeout=15)
    insert = r.json()
    insert_ok = insert.get('code', -1) == 0
    
    print(f"{stable}({len(stable)}c) / {child}: CREATE={create_ok} TABLE={table_ok} INSERT={insert_ok} code={insert.get('code')}")
