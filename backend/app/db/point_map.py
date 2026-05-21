"""SCADA 测点映射表 — 从 dams_config_cdpz 配置表提取

运行: python point_map.py
"""

import re
from collections import defaultdict


def parse_sql_file(filepath: str) -> dict:
    """解析 Navicat 导出的 SQL 文件, 提取测点映射"""
    model_points = defaultdict(dict)
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if not line.startswith("INSERT INTO"):
                continue
            match = re.search(r"VALUES \((.*)\);", line)
            if not match:
                continue
            parts = match.group(1).split("'")
            if len(parts) < 8:
                continue
            model = parts[3].strip()
            point_code = parts[5].strip().lower()
            point_name = parts[7].strip()
            if point_code and point_name:
                model_points[model][point_code] = point_name
    return dict(model_points)


# 完整映射表
MODEL_POINT_MAP = parse_sql_file("/root/.openclaw/workspace/nl2chart/hbz_yc.sql")

# 设备模型描述
MODEL_DESC = {
    "dq": "环境监测仪",
    "many1.0": "箱变测控",
    "many1.1": "箱变测控",
    "many1.2": "箱变测控",
    "many1.3": "箱变测控",
    "many1.4": "箱变测控",
}

# 默认使用 dq 模型的映射作为通用映射
POINT_MAP = MODEL_POINT_MAP.get("dq", {})

if __name__ == "__main__":
    print(f"解析到 {sum(len(v) for v in MODEL_POINT_MAP.values())} 个测点映射")
    print(f"设备模型数: {len(MODEL_POINT_MAP)}")
    for model, points in MODEL_POINT_MAP.items():
        print(f"\n模型 {model} ({MODEL_DESC.get(model, '未知')}): {len(points)} 个测点")
        for code, name in list(points.items())[:5]:
            print(f"  {code}: {name}")
