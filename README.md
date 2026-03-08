# 📈 Financial RAG System v2.1

**Enterprise-grade Financial Q&A System**

基于 Moonshot API + 行业报告检索的企业级金融问答系统

---

## ✨ Features

### 🔧 生产级特性

| 特性 | 描述 |
|------|------|
| 🏢 **企业架构** | 模块化设计、分层架构、松耦合 |
| 🔒 **安全防护** | API 限流、请求验证、日志审计 |
| 📊 **监控指标** | Prometheus 指标、健康检查 |
| ⚡ **性能优化** | 内存缓存、连接复用、异步处理 |
| 🧪 **测试支持** | Pydantic 模型、类型检查 |
| 📝 **完整文档** | OpenAPI 3.0、交互式文档 |

### 🛠 技术栈

```
Backend:     FastAPI + uvicorn
LLM:         Moonshot (Kimi) API
Frontend:    React (via CDN)
Logs:        JSON + Text
Deploy:      Docker / Nginx
```

---

## 📁 项目结构

```
financial-rag-system/
├── api/
│   ├── main.py              # 主入口 (生产级)
│   ├── routes/
│   │   └── api.py           # API 路由
│   ├── models/
│   │   └── schemas.py       # Pydantic 数据模型
│   └── core/
│       ├── moonshot_client.py  # Moonshot API 客户端
│       └── knowledge_base.py   # 知识库检索
├── config/
│   └── settings.py          # 企业级配置管理
├── utils/
│   ├── logger.py            # 企业级日志系统
│   └── rate_limit.py        # API 限流器
├── ui/
│   └── index.html           # Web UI
├── tests/                   # 测试目录
├── Dockerfile               # Docker 构建
├── docker-compose.yml       # Docker Compose
├── nginx.conf               # Nginx 配置
├── requirements.txt         # Python 依赖
└── README.md
```

---

## 🚀 快速部署

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

```bash
export MOONSHOT_API_KEY="your-api-key"
export APP_ENV=production
```

### 3. 启动服务

```bash
# 开发模式
python api/main.py

# 生产模式
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Docker 部署

```bash
docker build -t financial-rag .
docker run -p 8000:8000 -e MOONSHOT_API_KEY="your-key" financial-rag
```

---

## 📡 API 文档

### 问答接口

```bash
POST /api/query
Content-Type: application/json

{
    "question": "2026年人工智能行业趋势如何？",
    "history": [],
    "stream": false,
    "sources_limit": 5
}
```

### 健康检查

```bash
GET /api/health

Response:
{
    "status": "healthy",
    "version": "2.1.0",
    "components": {
        "api": {"status": "healthy"},
        "llm": {"status": "configured"}
    }
}
```

### 监控指标

```bash
GET /metrics
```

---

## 🔒 安全特性

1. **API 限流** - 默认 60 次/分钟
2. **请求验证** - Pydantic 模型校验
3. **日志审计** - JSON 格式日志
4. **错误处理** - 全局异常捕获

---

## 📊 性能指标

| 指标 | 目标值 |
|------|--------|
| 响应时间 | < 2s (不含 LLM) |
| 并发请求 | 100+ |
| 缓存命中率 | > 50% |
| 可用性 | 99.9% |

---

## 🧪 测试

```bash
# 运行测试
python -m pytest tests/

# 代码检查
python -m flake8 api/
python -m mypy api/
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 License

MIT License