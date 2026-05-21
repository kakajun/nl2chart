# NL2Chart 新能源SCADA可视化系统 — 后续开发文档

> 基于《AI自然语言可视化查询引擎市场调研报告》开源项目功能参考
> 参考项目：DB-GPT、WrenAI、SuperSonic、PyGWalker、Vanna、DeepBI、OpenChatBI

---

## 一、当前项目状态

| 维度 | 现状 |
|------|------|
| 项目 | `kakajun/nl2chart` |
| 前端 | Vite + Vue3，深色主题，ScadaDashboard组件 |
| 后端 | FastAPI，SQLite mock数据，4个API端点 |
| 数据 | 109万条记录，1电站(HBZ)，674测点，577时间点，覆盖2天 |
| 数据库 | SQLite (本地mock) → 目标 TDengine (生产) |
| 字段 | 工业编码 (a, aa, ab...) → 待映射到物理量 |

---

## 二、开源项目功能参考矩阵

### 2.1 对标项目核心能力

| 项目 | Stars | 我们可借鉴的功能 | 适用场景 |
|------|-------|------------------|----------|
| **DB-GPT** | 18.8k | Agent架构、RAG、Text2SQL、可视化报告生成、多模型支持 | 企业级AI数据分析平台 |
| **WrenAI** | 15k | Text-to-SQL + Text-to-Chart + Text-to-Insight，语义层驱动 | GenBI部署，语义层治理 |
| **SuperSonic** | 4.9k | 语义层驱动NLBI、Schema Mapper降幻觉、多轮对话、Headless BI | 中文ChatBI场景 |
| **PyGWalker** | 10.5k | 拖拽+自然语言查询，Tableau风格交互式UI | 数据探索、快速原型 |
| **Vanna** | 7-20k | Python RAG框架，3行代码集成Text2SQL | 快速集成 |
| **DeepBI** | 2.4k | 对话式数据科学家，多数据源AI分析 | AI原生BI |
| **OpenChatBI** | 562 | LangGraph架构ChatBI，MCP支持 | 企业BI对话分析 |

### 2.2 关键技术决策（参考报告4.2节）

| 决策 | 推荐方案 | 我们的选择 |
|------|----------|-----------|
| 语义层 | **必须** — 无语义层准确率<20%，有语义层>95% | ✅ 新能源SCADA语义层 |
| Agent架构 | LangGraph — 多步推理、自修复、工具编排 | ✅ FastAPI + 自定义Agent |
| Few-shot方式 | RAG Dynamic — 热更新、低维护 | ✅ 向量数据库 + RAG |
| 可视化规范 | Vega-Lite — 声明式、安全可验证 | ✅ ECharts (更贴合Vue生态) |
| SQL验证 | ExCoT执行反馈 — 提升10+百分点 | ✅ 后端校验 + 执行反馈 |
| 安全隔离 | 数据库层RLS | ✅ 只读账号 + 查询限制 |

---

## 三、开发路线图（4个Phase）

### Phase 1: 基础平台搭建（2-3周）—— **当前阶段**

**目标**：让系统能看数据、能查数据、能展示数据

#### 1.1 前端开发

| 功能模块 | 具体需求 | 参考项目 |
|----------|----------|----------|
| **电站总览大屏** | 实时功率、辐照度、温度、风速等KPI卡片 | SuperSonic KPI组件 |
| **时序趋势图** | 多测点曲线对比、时间范围选择、缩放 | PyGWalker 交互式图表 |
| **测点树导航** | 按设备/类型组织测点，支持搜索筛选 | DB-GPT 数据源导航 |
| **数据表格** | 原始数据查看、排序、导出CSV | WrenAI 数据表格 |

#### 1.2 后端开发

| 功能模块 | 具体需求 | 技术方案 |
|----------|----------|----------|
| **测点映射系统** | 将 a/aa/ab 映射到真实物理量（功率、辐照度等） | 配置文件 + 数据库表 |
| **历史数据查询API** | 按测点+时间范围查询，支持聚合 | FastAPI + SQL |
| **实时数据推送** | WebSocket 推送最新数据 | FastAPI WebSocket |
| **数据聚合接口** | 小时/日/月统计，最大值/最小值/平均值 | SQL GROUP BY |

#### 1.3 数据层

| 任务 | 说明 |
|------|------|
| 测点配置表导入 | 从 `hbz_config.sql` 解析测点信息 |
| 映射表构建 | 建立 point_code → 物理量名称/单位/类型的映射 |
| mock数据扩充 | 从2天扩展到7-30天，支持更多时间范围查询 |

---

### Phase 2: NL2Chart 核心能力（4-6周）

**目标**：自然语言 → SQL → 可视化图表

#### 2.1 Text2SQL 模块（参考 Vanna + DB-GPT）

```
用户输入: "今天 HBZ 电站的发电量趋势"
        ↓
[Intent Parser] 意图识别: 时序查询
        ↓
[Semantic Layer] 映射: 发电量 → point_code='a' (或映射后的字段)
        ↓
[SQL Generator] 生成: SELECT ts, value FROM scada_data 
                       WHERE station_code='HBZ' AND point_code='a' 
                       AND ts >= TODAY()
        ↓
[Query Executor] 执行 → 返回数据
        ↓
[Vis Generator] 生成图表配置 → ECharts 折线图
```

| 组件 | 技术方案 | 参考项目 |
|------|----------|----------|
| **Intent Parser** | 规则 + 轻量模型（关键词匹配意图类型） | SuperSonic Schema Mapper |
| **Semantic Layer** | 新能源领域知识库（指标/维度/同义词） | WrenAI MDL语义层 |
| **SQL Generator** | 模板引擎 + LLM（GPT-4o/Claude 3.5） | DB-GPT Text2SQL |
| **RAG Few-shot** | 向量数据库存储已验证查询示例 | Vanna RAG框架 |

#### 2.2 语义层设计（SCADA新能源专用）

```yaml
# 语义层配置示例
metrics:
  发电量:
    point_codes: ['a', 'aa']  # 多个测点可能对应同一概念
    unit: "kW"
    aggregation: [sum, avg, max]
    
  辐照度:
    point_codes: ['ab']
    unit: "W/m²"
    
  温度:
    point_codes: ['ac']
    unit: "°C"

dimensions:
  时间粒度: [原始, 小时, 日, 月]
  电站: [HBZ, 未来电站2, 未来电站3]
  设备类型: [逆变器, 汇流箱, 环境监测]

synonyms:
  发电量: [功率, 有功功率, 实时功率, power]
  辐照度: [辐射, 太阳辐射, irradiance]
```

#### 2.3 可视化生成（参考 PyGWalker + WrenAI）

| 查询意图 | 自动选择图表类型 | 配置参数 |
|----------|------------------|----------|
| 时序趋势 | 折线图 (Line) | X=时间, Y=数值, 多系列对比 |
| 设备对比 | 柱状图 (Bar) | X=设备, Y=聚合值 |
| 相关性分析 | 散点图 (Scatter) | X=测点A, Y=测点B |
| 数据分布 | 面积图/热力图 | 时间×数值密度 |
| 占比分析 | 饼图/环形图 | 各部分占比 |

---

### Phase 3: AI Agent 增强（3-4周）

**目标**：从"单次查询"升级到"对话式分析"

#### 3.1 Agent架构（参考 DB-GPT + OpenChatBI）

```
用户: "HBZ电站这周发电量怎么样？"
Agent: "本周平均发电量 1.2MW，较上周下降 5%。需要查看具体趋势吗？"
用户: "和辐照度对比一下"
Agent: [自动生成双Y轴对比图：发电量 vs 辐照度]
用户: "下降的原因是什么？"
Agent: [分析相关性：发电量与辐照度相关系数 0.95，
       推测下降主要由天气因素导致。需要查看温度数据吗？]
```

| Agent能力 | 实现方案 | 参考项目 |
|-----------|----------|----------|
| **多轮对话** | 对话状态管理 + 上下文关联 | SuperSonic 多轮对话 |
| **意图切换** | 识别新意图 vs 追问意图 | DB-GPT Agent |
| **错误自修复** | SQL执行失败 → 自动修正重试 | LangGraph ReAct |
| **洞察生成** | 数据异常检测 + 自然语言解读 | WrenAI Text-to-Insight |

#### 3.2 RAG 示例库（参考 Vanna）

```python
# 已验证查询示例（Few-shot）
examples = [
    {
        "question": "今天发电量",
        "sql": "SELECT ts, value FROM scada_data WHERE point_code='a' AND ts>=DATE('now')",
        "chart": "line",
        "verified": True
    },
    {
        "question": "本周各设备功率对比",
        "sql": "SELECT equ_code, AVG(value) FROM scada_data WHERE ... GROUP BY equ_code",
        "chart": "bar",
        "verified": True
    }
]
```

**RAG流程**：
1. 用户输入 → 向量化
2. 检索最相似的3个已验证示例
3. 将示例注入Prompt → LLM生成SQL
4. 执行 → 验证 → 入库（反馈闭环）

---

### Phase 4: 企业级功能（3-4周）

**目标**：生产可用，多电站支持，安全可靠

#### 4.1 多电站/多数据源支持

| 功能 | 说明 |
|------|------|
| 电站切换 | 支持 HBZ、未来电站2、未来电站3 |
| 数据源适配 | TDengine 为主，SQLite 为测试 |
| 联邦查询 | 跨电站数据对比（未来） |

#### 4.2 安全与权限

| 功能 | 方案 |
|------|------|
| 只读限制 | 数据库只读账号，禁止DELETE/UPDATE |
| 查询限制 | 最大返回行数、时间范围限制 |
| SQL注入防护 | 参数化查询 + 白名单校验 |
| 审计日志 | 记录所有查询请求和生成的SQL |

#### 4.3 告警与预测（老爷原有目标）

| 功能 | 说明 |
|------|------|
| 阈值告警 | 功率突降、温度异常等规则告警 |
| 趋势预测 | 基于历史数据预测未来发电量 |
| 异常检测 | 统计方法检测数据异常点 |

---

## 四、技术栈确认

### 4.1 已确定

| 层级 | 技术 | 状态 |
|------|------|------|
| 前端框架 | Vite + Vue3 + ECharts | ✅ 已搭建 |
| 后端框架 | FastAPI + Python | ✅ 已搭建 |
| 数据存储 | TDengine (生产) / SQLite (测试) | ✅ 已确认 |
| 代码规范 | oxfmt + oxlint | ✅ 已配置 |

### 4.2 待引入

| 技术 | 用途 | 引入时机 |
|------|------|----------|
| **OpenAI/Claude API** | LLM文本生成SQL | Phase 2 |
| **ChromaDB/Pinecone** | RAG向量存储 | Phase 2 |
| **LangGraph** | Agent编排（可选） | Phase 3 |
| **WebSocket** | 实时数据推送 | Phase 1 |
| **Pandas** | 数据处理/聚合 | Phase 1 |
| **SQLAlchemy** | ORM/多数据库适配 | Phase 1 |

---

## 五、详细任务清单（Phase 1 拆解）

### Week 1: 测点映射 + 基础API

- [ ] 解析 `hbz_config.sql` 提取测点配置
- [ ] 设计 `point_map` 表结构（code → name/unit/type/equipment）
- [ ] 编写测点映射导入脚本
- [ ] 完善 `/api/scada/metrics/{station_code}` 接口（返回带物理名称的数据）
- [ ] 新增 `/api/scada/points/{station_code}` 接口（返回测点列表）
- [ ] 前端：测点树组件开发

### Week 2: 前端Dashboard + 时序图

- [ ] 前端：KPI卡片组件（实时功率/辐照度/温度/风速）
- [ ] 前端：ECharts 折线图组件（时序趋势）
- [ ] 前端：时间范围选择器（今天/本周/本月/自定义）
- [ ] 后端：历史数据查询API（支持时间范围+测点多选）
- [ ] 后端：数据聚合API（小时/日/月统计）

### Week 3: 数据扩充 + 集成测试

- [ ] mock数据生成器扩充到7-30天
- [ ] WebSocket实时数据推送
- [ ] 前后端联调
- [ ] 测试：不同时间粒度查询
- [ ] 测试：多测点对比
- [ ] 文档：API文档 + 部署说明

---

## 六、关键风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 测点映射不完整 | 查询结果不准确 | 建立映射审核流程，支持人工修正 |
| Text2SQL准确率 | NL查询理解错误 | 先规则+模板，再逐步引入LLM |
| TDengine连接稳定性 | 生产数据中断 | 本地缓存 + 降级到mock数据 |
| 性能（100万+数据） | 查询慢 | 数据库索引 + 分页 + 预聚合 |

---

## 七、参考来源

- DB-GPT: https://github.com/eosphoros-ai/DB-GPT
- WrenAI: https://github.com/Canner/WrenAI
- SuperSonic: https://github.com/tencentmusic/supersonic
- PyGWalker: https://github.com/Kanaries/pygwalker
- Vanna: https://github.com/vanna-ai/vanna
- 《AI自然语言可视化查询引擎市场调研报告》2025年7月

---

> 文档生成时间：2026-05-22
> 适用项目：nl2chart 新能源SCADA可视化系统
