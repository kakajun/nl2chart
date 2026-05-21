"""TDengine 数据库连接与查询封装"""

import os
from contextlib import contextmanager
from typing import Any

try:
    import taosws
except ImportError:
    taosws = None

# jdbc:TAOS-WS://192.168.0.250:6041/station_data
TD_HOST = os.getenv("TD_HOST", "192.168.0.250")
TD_PORT = int(os.getenv("TD_PORT", "6041"))
TD_DB = os.getenv("TD_DB", "station_data")
TD_USER = os.getenv("TD_USER", "root")
TD_PASS = os.getenv("TD_PASS", "taosdata")


class TDEngineClient:
    """TDengine WS 连接客户端"""

    def __init__(
        self,
        host: str = TD_HOST,
        port: int = TD_PORT,
        database: str = TD_DB,
        user: str = TD_USER,
        password: str = TD_PASS,
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self._conn = None

    def connect(self):
        if taosws is None:
            raise RuntimeError("taos-ws-py 未安装: pip install taos-ws-py")
        ws_url = f"ws://{self.host}:{self.port}"
        self._conn = taosws.connect(ws_url, self.user, self.password, self.database)
        return self

    def query(self, sql: str) -> list[dict[str, Any]]:
        if not self._conn:
            self.connect()
        result = self._conn.query(sql)
        cols = [c.name for c in result.fields]
        rows = []
        for row in result:
            rows.append(dict(zip(cols, row)))
        return rows

    def execute(self, sql: str) -> int:
        if not self._conn:
            self.connect()
        return self._conn.execute(sql)

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


@contextmanager
def get_td_client():
    client = TDEngineClient()
    try:
        client.connect()
        yield client
    finally:
        client.close()
