import requests

URL = 'http://10.204.252.13:6041/rest/sql/station_data2'
HEADERS = {'Authorization': 'Basic cm9vdDp0YW9zZGF0YQ==', 'Content-Type': 'text/plain'}

for length in range(18, 27):
    name = 's' * length
    # DROP
    requests.post(URL, headers=HEADERS, data=f"DROP STABLE IF EXISTS {name}", timeout=10)
    # CREATE
    r = requests.post(URL, headers=HEADERS, data=f"CREATE STABLE {name} (ts TIMESTAMP, a DOUBLE) TAGS (equ VARCHAR(50))", timeout=15)
    create_ok = r.json().get('code', -1) == 0
    # TABLE
    r = requests.post(URL, headers=HEADERS, data=f"CREATE TABLE t USING {name} TAGS ('t')", timeout=15)
    table_ok = r.json().get('code', -1) == 0
    # INSERT
    r = requests.post(URL, headers=HEADERS, data=f"INSERT INTO t (ts, a) VALUES ('2026-05-21 22:00:00', 1.0)", timeout=15)
    insert_ok = r.json().get('code', -1) == 0
    
    status = "OK" if (create_ok and table_ok and insert_ok) else "FAIL"
    print(f"{length:2d} chars: {status} (CREATE={create_ok}, TABLE={table_ok}, INSERT={insert_ok})")
