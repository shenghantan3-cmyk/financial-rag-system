# 📈 Financial RAG System

基于行业研究报告的**金融领域检索增强生成（RAG）问答系统**。

## ✨ 功能特性

- 💬 **智能问答** - 基于金融报告的专业问答
- 🎨 **美观 UI** - 现代渐变 Dark Mode 界面
- 📱 **响应式** - 支持 PC 和移动端
- 🔍 **混合检索** - Embedding + BM25 关键字
- 📝 **对话记忆** - 维护上下文连贯性
- 📊 **溯源标注** - 注明信息来源
- 🐳 **Docker 部署** - 一键容器化部署
- 🌐 **公网暴露** - 支持 Cloudflare Tunnel

---

## 🚀 快速启动

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd finance_rag

# 2. 启动服务
chmod +x start.sh
./start.sh
```

访问 http://localhost:8000

### 方式二：手动运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端
python api/main.py

# 访问
# 打开 ui/index.html
```

---

## 📁 项目结构

```
finance_rag/
├── api/
│   └── main.py              # FastAPI 后端
├── ui/
│   └── index.html           # Web 界面
├── data/
│   ├── vector_db/           # Qdrant 向量数据库
│   └── parent_store/        # Parent 块存储
├── nginx/
│   └── nginx.conf           # Nginx 配置
├── scripts/
│   ├── chat.mjs             # CLI 聊天
│   └── setup_db.mjs         # 数据库初始化
├── Dockerfile               # Docker 构建
├── docker-compose.yml       # Docker Compose
├── docker-compose.public.yml # 公网部署配置
├── start.sh                 # 快速启动脚本
├── requirements.txt         # Python 依赖
└── README.md
```

---

## 🌐 公网部署

### 方案一：Cloudflare Tunnel（免费，推荐）

```bash
# 1. 注册 Cloudflare Zero Trust
#    https://one.dash.cloudflare.com/

# 2. 创建 Tunnel，获取 Token

# 3. 配置环境变量
echo 'CLOUDFLARE_TOKEN=your-tunnel-token' > .env

# 4. 启动公网服务
docker compose -f docker-compose.yml -f docker-compose.public.yml up -d
```

访问隧道URL，即可公网访问！

### 方案二：部署到云服务器

```bash
# 1. 构建镜像
docker build -t financial-rag .

# 2. 运行容器
docker run -d \
  --name financial-rag \
  -p 80:8000 \
  -v $(pwd)/data:/app/data \
  financial-rag
```

### 方案三：使用反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## ⚙️ 配置说明

### 环境变量

在 `.env` 文件中配置：

```env
# LLM 选择（选择其一）

# OpenAI
OPENAI_API_KEY=sk-xxx

# Moonshot/Kimi
MOONSHOT_API_KEY=sk-xxx

# Ollama (本地)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b-instruct
```

### 修改 LLM

编辑 `api/main.py` 中的 `ask()` 函数，替换为你的 LLM 调用。

---

## 📊 系统架构

```
                    ┌─────────────────────┐
                    │   🖥️ 浏览器用户       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   🌐 Nginx / CDN     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   🐳 Docker 容器     │
                    │  ┌───────────────┐  │
                    │  │  FastAPI API   │  │
                    │  │  (8000端口)    │  │
                    │  └───────┬───────┘  │
                    │          │          │
                    │  ┌───────▼───────┐  │
                    │  │   Qdrant DB   │  │
                    │  │  (向量检索)    │  │
                    │  └───────────────┘  │
                    └─────────────────────┘
```

---

## 📦 依赖数据

系统会从以下位置自动导入报告：

- `~/finance_reports/` - 每日金融报告
- `docs/` - 自定义 PDF/Markdown 文件
- `markdown/` - 转换后的文档

---

## 🔧 常用命令

```bash
# 启动服务
./start.sh

# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 更新代码
docker compose up -d --build

# 清理数据
rm -rf data/vector_db/*
```

---

## 🛠️ 开发计划

- [ ] WebSocket 实时通信
- [ ] 用户认证系统
- [ ] 文档上传处理
- [ ] 多模型切换
- [ ] 性能优化

---

## 📄 许可证

MIT License