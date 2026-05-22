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

# 去掉测点名称中的 _1/_2 后缀（统一为通用名称）
for model, points in MODEL_POINT_MAP.items():
    for code in list(points.keys()):
        name = points[code]
        # 去掉 _1, _2, _3... 后缀
        clean_name = re.sub(r'_\d+$', '', name)
        points[code] = clean_name

# 设备模型描述
MODEL_DESC = {
    "dq": "环境监测仪",
    "many1.0": "箱变测控",
    "many1.1": "箱变测控",
    "many1.2": "箱变测控",
    "many1.3": "箱变测控",
    "many1.4": "箱变测控",
}

# 合并所有模型的测点映射（many1.x 优先，dq 最后覆盖环境监测部分）
POINT_MAP = {}
# 先加载 many1.x 模型（箱变/逆变器测点）
for model, points in MODEL_POINT_MAP.items():
    if model.startswith('many'):
        POINT_MAP.update(points)
# 再加载 dq 模型（环境监测测点），但只覆盖 a~am 范围内的编码
env_codes = set()
for code in list('abcdefghijklmnopqrstuvwxyz') + ['aa','ab','ac','ad','ae','af','ag','ah','ai','aj','ak','al','am']:
    env_codes.add(code)
for code, name in MODEL_POINT_MAP.get("dq", {}).items():
    if code in env_codes:
        POINT_MAP[code] = name
    elif code not in POINT_MAP:
        POINT_MAP[code] = name

# 如果从 hbz_yc.sql 没有解析到 many1.0 的测点，从 hbz_config.sql 补充
if not any(k.startswith('many') for k in MODEL_POINT_MAP.keys()):
    import re
    def parse_hbz_config(filepath):
        inv_points = {}
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.startswith("INSERT INTO"):
                    continue
                vals_match = re.search(r'VALUES \((.*)\);', line)
                if not vals_match:
                    continue
                vals = vals_match.group(1)
                parts = []
                current = ''
                in_quote = False
                for c in vals:
                    if c == "'":
                        in_quote = not in_quote
                        current += c
                    elif c == ',' and not in_quote:
                        parts.append(current.strip())
                        current = ''
                    else:
                        current += c
                if current:
                    parts.append(current.strip())
                
                if len(parts) < 40:
                    continue
                
                model = parts[1].strip("'") if len(parts) > 1 else ''
                cdbh = parts[2].strip("'") if len(parts) > 2 else ''
                cdmc = parts[3].strip("'") if len(parts) > 3 else ''
                dtype = parts[16].strip("'") if len(parts) > 16 else ''
                sbbh = parts[38].strip("'") if len(parts) > 38 else ''
                
                if sbbh == 'NULL':
                    sbbh = ''
                
                if model.startswith('many') and cdbh and cdmc:
                    base_name = re.sub(r'_\d+$', '', cdmc)
                    inv_points[cdbh.lower()] = base_name
        return inv_points
    
    config_points = parse_hbz_config("/root/.openclaw/workspace/nl2chart/hbz_config.sql")
    POINT_MAP.update(config_points)

# dq 环境监测测点最后更新（确保环境监测仪测点正确）
for code, name in MODEL_POINT_MAP.get("dq", {}).items():
    POINT_MAP[code] = name

if __name__ == "__main__":
    print(f"解析到 {sum(len(v) for v in MODEL_POINT_MAP.values())} 个测点映射")
    print(f"设备模型数: {len(MODEL_POINT_MAP)}")
    for model, points in MODEL_POINT_MAP.items():
        print(f"\n模型 {model} ({MODEL_DESC.get(model, '未知')}): {len(points)} 个测点")
        for code, name in list(points.items())[:5]:
            print(f"  {code}: {name}")
