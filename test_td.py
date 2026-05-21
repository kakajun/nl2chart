import taosws

HOST = "10.204.252.13"
PORT = 6041  # REST/WebSocket 端口
USER = "root"
PASS = "taosdata"
DB = "station_data"

try:
    conn = taosws.connect(f"taosws://{USER}:{PASS}@{HOST}:{PORT}/{DB}")
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES")
    rows = cursor.fetchall()
    print("✅ 连接成功")
    print("数据库列表:", [r[0] for r in rows])
    
    cursor.execute("USE station_data")
    cursor.execute("SELECT COUNT(*) FROM stable_es_station_pjygcdz_equ")
    print("超级表记录数:", cursor.fetchall())
except Exception as e:
    print(f"❌ 连接失败: {e}")
