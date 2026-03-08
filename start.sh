#!/bin/bash
set -e

echo """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║    🏦 Financial RAG System - 快速部署脚本                          ║
║                                                                   ║
║    支持本地运行和公网部署                                          ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
"""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装，请先安装 Docker${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装${NC}"
    exit 1
fi

# Use docker compose if available (v2), otherwise docker-compose
COMPOSE_CMD="docker compose"
if ! docker compose version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
fi

# Change to script directory
cd "$(dirname "$0")"

# Create required directories
echo -e "\n${YELLOW}📁 创建必要目录...${NC}"
mkdir -p data/vector_db data/parent_store logs

# Build and start services
echo -e "\n${YELLOW}🏗️  构建 Docker 镜像...${NC}"
$COMPOSE_CMD build

# Start services
echo -e "\n${YELLOW}🚀  启动服务...${NC}"
$COMPOSE_CMD up -d

# Wait for services to be ready
echo -e "\n${YELLOW}⏳  等待服务启动...${NC}"
sleep 5

# Check health
echo -e "\n${YELLOW}🔍  检查服务状态...${NC}"
$COMPOSE_CMD ps

# Get URLs
echo -e """
${GREEN}═══════════════════════════════════════════════════════════════${NC}

${GREEN}✅ 服务启动成功！${NC}

📡 访问地址：
   - 本地:   http://localhost:8000
   - API:   http://localhost:8000/docs
   - 健康:  http://localhost:8000/health

${YELLOW}═══════════════════════════════════════════════════════════════${NC}

🛠️  常用命令：

   查看日志:  $COMPOSE_CMD logs -f
   停止服务:  $COMPOSE_CMD down
   重启服务:  $COMPOSE_CMD restart
   更新代码:  $COMPOSE_CMD up -d --build

${YELLOW}═══════════════════════════════════════════════════════════════${NC}

💡 下一步 - 暴露公网（可选）：

   1. 注册 Cloudflare Zero Trust
   2. 获取 Tunnel Token: https://one.dash.cloudflare.com/
   3. 创建 .env 文件：
      echo 'CLOUDFLARE_TOKEN=你的token' > .env
   4. 使用公网配置启动：
      $COMPOSE_CMD -f docker-compose.yml -f docker-compose.public.yml up -d

${GREEN}═══════════════════════════════════════════════════════════════${NC}
"""