import requests

URL = 'http://10.204.252.13:6041/rest/sql/station_data2'
HEADERS = {'Authorization': 'Basic cm9vdDp0YW9zZGF0YQ==', 'Content-Type': 'text/plain'}

# 创建不含 'bit' 的 39 字段超级表
fields = [
    'ts TIMESTAMP',
    '`a` DOUBLE', '`b` DOUBLE', '`c` DOUBLE', '`d` DOUBLE', '`e` DOUBLE',
    '`f` DOUBLE', '`g` DOUBLE', '`h` DOUBLE', '`i` DOUBLE', '`j` DOUBLE',
    '`k` DOUBLE', '`l` DOUBLE', '`m` DOUBLE', '`n` DOUBLE', '`o` DOUBLE',
    '`p` DOUBLE', '`q` DOUBLE', '`r` DOUBLE', '`s` DOUBLE', '`t` DOUBLE',
    '`u` DOUBLE', '`v` DOUBLE', '`w` DOUBLE', '`x` DOUBLE', '`y` DOUBLE',
    '`z` DOUBLE', '`aa` DOUBLE', '`ab` DOUBLE', '`ac` DOUBLE', '`ad` DOUBLE',
    '`ae` DOUBLE', '`af` DOUBLE', '`ag` DOUBLE', '`ah` DOUBLE', '`ai` DOUBLE',
    'cold VARCHAR(255)', 'bitfield VARCHAR(255)', 'other VARCHAR(255)'
]
fd = ', '.join(fields)

r = requests.post(URL, headers=HEADERS, data="DROP STABLE IF EXISTS test_stable", timeout=15)
print('DROP:', r.json().get('code'))

r = requests.post(URL, headers=HEADERS, data=f"CREATE STABLE test_stable ({fd}) TAGS (equ VARCHAR(50), station VARCHAR(50))", timeout=15)
print('CREATE:', r.json().get('code'))

r = requests.post(URL, headers=HEADERS, data="CREATE TABLE test1 USING test_stable TAGS ('test1', 'hbz')", timeout=15)
print('CREATE TABLE:', r.json().get('code'))

r = requests.post(URL, headers=HEADERS, data="INSERT INTO test1 (ts, a, e, h) VALUES ('2026-05-21 22:00:00', 300.5, 25.0, 1000.0)", timeout=15)
print('INSERT:', r.json())
