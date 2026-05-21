import requests

URL = 'http://10.204.252.13:6041/rest/sql/station_data2'
H = {'Authorization': 'Basic cm9vdDp0YW9zZGF0YQ==', 'Content-Type': 'text/plain'}

# 测试下划线在子表名
for child in ['hj01', 'h_j01', 'HBZHJ01', 'HBZ_HJ01']:
    # 先删除
    requests.post(URL, headers=H, data=f"DROP TABLE IF EXISTS {child}", timeout=10)
    
    # 创建
    r = requests.post(URL, headers=H, data=f"CREATE TABLE {child} USING scada_equ TAGS ('{child}', 'hbz')", timeout=15)
    create_ok = r.json().get('code', -1) == 0
    
    # INSERT
    r = requests.post(URL, headers=H, data=f"INSERT INTO {child} (ts, a) VALUES ('2026-05-21 22:00:00', 1.0)", timeout=15)
    insert = r.json()
    insert_ok = insert.get('code', -1) == 0
    
    print(f"{child}: CREATE={create_ok} INSERT={insert_ok} code={insert.get('code')}")
