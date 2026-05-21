import requests

URL = "http://10.204.252.13:6041/rest/sql"
HEADERS = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ==", "Content-Type": "text/plain"}

def sql(db, query):
    r = requests.post(f"{URL}/{db}", headers=HEADERS, data=query, timeout=15)
    return r.json()

# 创建新库
print("创建 station_data2...")
print(sql("", "CREATE DATABASE IF NOT EXISTS station_data2"))

# 创建简化版超级表
print("\n创建超级表...")
print(sql("station_data2", "CREATE STABLE IF NOT EXISTS scada (ts TIMESTAMP, `a` DOUBLE, `e` DOUBLE, `h` DOUBLE) TAGS (equ VARCHAR(50), station VARCHAR(50))"))

# 创建子表
print("\n创建子表...")
print(sql("station_data2", "CREATE TABLE IF NOT EXISTS h1 USING scada TAGS ('h1', 'hbz')"))

# INSERT
print("\n测试 INSERT...")
print(sql("station_data2", "INSERT INTO h1 (ts, a, e, h) VALUES ('2026-05-21 22:00:00', 300.0, 25.0, 1000.0)"))

# SELECT
print("\n测试 SELECT...")
print(sql("station_data2", "SELECT * FROM h1"))

# COUNT
print("\n超级表 COUNT...")
print(sql("station_data2", "SELECT COUNT(*) FROM scada"))
