"""TDengine 连接模块 — 连接真实 SCADA 数据库"""

import taosws
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

# TDengine 连接配置
TD_HOST = os.getenv("TD_HOST", "192.168.0.250")
TD_PORT = os.getenv("TD_PORT", "6041")
TD_DB = os.getenv("TD_DB", "station_data")
TD_USER = os.getenv("TD_USER", "root")
TD_PASS = os.getenv("TD_PASS", "taosdata")

# 备用: ZeroTier 地址
TD_HOST_ZT = os.getenv("TD_HOST_ZT", "10.204.252.13")

CONNECTION_STRING = f"taosws://{TD_HOST}:{TD_PORT}/{TD_DB}"
CONNECTION_STRING_ZT = f"taosws://{TD_HOST_ZT}:{TD_PORT}/{TD_DB}"


class TDEngineClient:
    """TDengine 客户端 — 连接电站 SCADA 数据库"""

    def __init__(self, use_zt: bool = False):
        self.conn = None
        self.cursor = None
        self.connected = False
        self.conn_str = CONNECTION_STRING_ZT if use_zt else CONNECTION_STRING

    def connect(self) -> bool:
        """建立连接"""
        try:
            self.conn = taosws.connect(self.conn_str)
            self.cursor = self.conn.cursor()
            self.connected = True
            return True
        except Exception as e:
            print(f"[TDengine] 连接失败 ({self.conn_str}): {e}")
            self.connected = False
            return False

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.connected = False

    def test(self) -> bool:
        """测试连接"""
        if not self.connected and not self.connect():
            return False
        try:
            self.cursor.execute("SELECT 1")
            self.cursor.fetchall()
            return True
        except Exception as e:
            print(f"[TDengine] 测试失败: {e}")
            self.connected = False
            return False

    def list_tables(self) -> List[str]:
        """列出所有超级表/子表"""
        if not self.connected and not self.connect():
            return []
        try:
            self.cursor.execute("SHOW TABLES")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"[TDengine] 列出表失败: {e}")
            return []

    def get_table_schema(self, table_name: str) -> List[Dict]:
        """获取表结构"""
        if not self.connected and not self.connect():
            return []
        try:
            self.cursor.execute(f"DESCRIBE {table_name}")
            columns = []
            for row in self.cursor.fetchall():
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "length": row[2],
                    "note": row[3] if len(row) > 3 else "",
                })
            return columns
        except Exception as e:
            print(f"[TDengine] 获取结构失败: {e}")
            return []

    def query_latest(self, table_name: str, limit: int = 100) -> List[Dict]:
        """查询最新数据"""
        if not self.connected and not self.connect():
            return []
        try:
            self.cursor.execute(f"""
                SELECT * FROM {table_name}
                ORDER BY ts DESC
                LIMIT {limit}
            """)
            rows = self.cursor.fetchall()
            # 获取列名
            col_names = [desc[0] for desc in self.cursor.description]
            result = []
            for row in rows:
                result.append(dict(zip(col_names, row)))
            return result
        except Exception as e:
            print(f"[TDengine] 查询失败: {e}")
            return []

    def query_range(
        self,
        table_name: str,
        start_time: datetime,
        end_time: datetime,
        columns: Optional[List[str]] = None,
    ) -> List[Dict]:
        """按时间范围查询"""
        if not self.connected and not self.connect():
            return []
        try:
            cols = ", ".join(columns) if columns else "*"
            start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

            self.cursor.execute(f"""
                SELECT {cols} FROM {table_name}
                WHERE ts >= '{start_str}' AND ts <= '{end_str}'
                ORDER BY ts
            """)
            rows = self.cursor.fetchall()
            col_names = [desc[0] for desc in self.cursor.description]
            result = []
            for row in rows:
                result.append(dict(zip(col_names, row)))
            return result
        except Exception as e:
            print(f"[TDengine] 范围查询失败: {e}")
            return []

    def query_station_data(
        self,
        table_name: str = "hbz_yc",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        point_codes: Optional[List[str]] = None,
    ) -> List[Dict]:
        """查询电站测点数据 — 适配 SCADA 表结构

        典型表结构:
        - ts: 时间戳
        - a, b, c...: 测点值 (FLOAT)
        - equ_code: 设备编码
        """
        if not self.connected and not self.connect():
            return []

        try:
            # 先获取表结构
            schema = self.get_table_schema(table_name)
            if not schema:
                return []

            # 确定哪些列是测点 (排除 ts, equ_code 等元数据列)
            meta_cols = {"ts", "equ_code", "station_code", "tbname"}
            point_cols = [s["name"] for s in schema if s["name"] not in meta_cols]

            # 如果指定了测点编码，只查这些列
            if point_codes:
                point_cols = [c for c in point_cols if c in point_codes]

            if not point_cols:
                return []

            cols_sql = ", ".join(["ts", "equ_code"] + point_cols)

            # 构建 WHERE
            where_parts = []
            if start_time and end_time:
                start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
                end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
                where_parts.append(f"ts >= '{start_str}' AND ts <= '{end_str}'")

            where_sql = " AND ".join(where_parts) if where_parts else "1=1"

            sql = f"SELECT {cols_sql} FROM {table_name} WHERE {where_sql} ORDER BY ts"
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()

            # 获取列名
            col_names = [desc[0] for desc in self.cursor.description]

            result = []
            for row in rows:
                row_dict = dict(zip(col_names, row))
                # 展开为每条记录一个测点的格式（兼容现有API）
                ts = row_dict.get("ts")
                equ_code = row_dict.get("equ_code", "HBZ")
                for col in point_cols:
                    if col in row_dict and row_dict[col] is not None:
                        result.append({
                            "ts": ts,
                            "station_code": "HBZ",
                            "equ_code": equ_code,
                            "point_code": col,
                            "value": float(row_dict[col]),
                        })

            return result

        except Exception as e:
            print(f"[TDengine] 电站数据查询失败: {e}")
            return []


# 全局客户端实例
_td_client: Optional[TDEngineClient] = None


def get_td_client(use_zt: bool = False) -> TDEngineClient:
    """获取 TDengine 客户端实例（单例）"""
    global _td_client
    if _td_client is None:
        _td_client = TDEngineClient(use_zt=use_zt)
    return _td_client


def check_tdengine() -> Dict:
    """检查 TDengine 连接状态"""
    client = get_td_client(use_zt=True)  # 优先尝试 ZeroTier 地址
    ok = client.test()
    if not ok:
        # 回退到原始地址
        client = get_td_client(use_zt=False)
        ok = client.test()

    if ok:
        tables = client.list_tables()
        return {
            "connected": True,
            "host": TD_HOST_ZT if client.conn_str == CONNECTION_STRING_ZT else TD_HOST,
            "database": TD_DB,
            "tables": tables[:20],  # 只返回前20个表
            "table_count": len(tables),
        }
    else:
        return {
            "connected": False,
            "host": TD_HOST,
            "database": TD_DB,
            "error": "无法连接 TDengine，请检查网络或服务状态",
        }


if __name__ == "__main__":
    # 测试连接
    print("=" * 50)
    print("TDengine 连接测试")
    print("=" * 50)
    status = check_tdengine()
    print(f"连接状态: {'✅ 在线' if status['connected'] else '❌ 离线'}")
    print(f"目标主机: {status['host']}")
    print(f"数据库: {status['database']}")
    if status['connected']:
        print(f"表数量: {status['table_count']}")
        print(f"表列表: {', '.join(status['tables'][:10])}")
    else:
        print(f"错误: {status.get('error', '未知错误')}")
    print("=" * 50)
