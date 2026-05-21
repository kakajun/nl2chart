# NL2Chart

自然语言转可视化图表引擎 (Natural Language to Chart Visualization Engine)

## 项目简介

基于 AI 自然语言查询的可视化分析平台。用户通过自然语言描述数据需求，系统自动生成 SQL、执行查询并渲染交互式图表。

## 技术栈

- **前端**: Vite + Vue 3 + TypeScript
- **后端**: FastAPI + Python 3
- **格式化**: oxlint + oxfmt

## 目录结构

```
nl2chart/
├── frontend/          # Vue3 前端应用
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── backend/           # FastAPI 后端服务
│   ├── app/
│   ├── requirements.txt
│   └── run.py
└── docs/              # 调研文档
    └── AI自然语言可视化查询引擎市场调研报告.docx
```

## 快速开始

### 前端

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

### 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py      # http://localhost:8000
```

### 代码规范

```bash
cd frontend
npm run format      # 格式化代码
npm run lint        # 静态检查
```

## API 文档

后端启动后访问: http://localhost:8000/docs
