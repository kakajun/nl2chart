import requests

URL = 'http://10.204.252.13:6041/rest/sql/station_data2'
H = {'Authorization': 'Basic cm9vdDp0YW9zZGF0YQ==', 'Content-Type': 'text/plain'}
s = requests.Session()

# 测试多 VALUES 批量插入
sql = """INSERT INTO HBZ_HJ01 (ts, a, b, e, h, j) VALUES
  ('2026-04-22 05:00:00', 300, 25, 5, 230, 235),
  ('2026-04-22 05:30:00', 301, 25, 5, 231, 236),
  ('2026-04-22 06:00:00', 302, 25, 5, 232, 237),
  ('2026-04-22 06:30:00', 303, 25, 5, 233, 238),
  ('2026-04-22 07:00:00', 304, 25, 5, 234, 239)"""

r = s.post(URL, headers=H, data=sql, timeout=15)
print('Multi-values:', r.json())

# COUNT
r3 = s.post(URL, headers=H, data='SELECT COUNT(*) FROM scada_equ', timeout=10)
print('COUNT:', r3.json())
