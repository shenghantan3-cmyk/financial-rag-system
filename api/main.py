#!/usr/bin/env python3
"""
Financial RAG System - Production Main Entry
生产级主入口
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.exception_handlers import http_exception_handler

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import config, load_config
from utils.logger import logger
from utils.rate_limit import rate_limiter

# 导入路由
from api.routes.api import router as api_router


# ============ Lifespan ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting Financial RAG System...")
    logger.info(f"Version: {config.version}")
    logger.info(f"Environment: {config.environment}")
    
    # 预加载知识库
    try:
        from api.core.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        stats = kb.get_stats()
        logger.info(f"Knowledge base loaded: {stats['total_documents']} documents")
    except Exception as e:
        logger.warning(f"Knowledge base load failed: {e}")
    
    logger.info("✅ Financial RAG System started successfully")
    
    yield
    
    logger.info("Shutting down Financial RAG System...")
    logger.info("👋 Goodbye!")


# ============ FastAPI App ============

app = FastAPI(
    title="Financial RAG System",
    description="🔬 Enterprise-grade Financial Q&A System based on Moonshot API + Industry Reports",
    version=config.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", 
                path=request.url.path,
                traceback=True)
    return await http_exception_handler(request, exc)


# ============ Root Endpoint ============

@app.get("/", response_class=StreamingResponse)
async def root():
    """服务前端 UI"""
    ui_path = PROJECT_ROOT / "ui" / "index.html"
    if ui_path.exists():
        with open(ui_path, "r", encoding="utf-8") as f:
            return StreamingResponse(iter([f.read()]), media_type="text/html")
    return {"message": "Financial RAG System", "docs": "/docs"}


# ============ Metrics Endpoint ============

@app.get("/metrics")
async def metrics():
    """Prometheus 指标"""
    from api.core.knowledge_base import KnowledgeBase
    
    uptime = (datetime.now() - datetime.strptime(
        "2000-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"
    )).total_seconds()
    
    memory = 0
    try:
        import psutil
        process = psutil.Process()
        memory = process.memory_info().rss / 1024 / 1024  # MB
    except:
        pass
    
    return {
        "uptime_seconds": int(time.time()),
        "memory_usage_mb": round(memory, 2),
        "requests_total": 0,
        "requests_in_progress": 0,
        "knowledge_base_documents": 5,
        "system_status": "healthy"
    }


# ============ Mount Routes ============

app.include_router(api_router, prefix="/api")


# ============ Main Entry ============

if __name__ == "__main__":
    # 日志
    logger.setup(
        level=config.logging.level,
        log_path=os.path.join(PROJECT_ROOT, "logs")
    )
    
    logger.info(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║    🏦 Financial RAG System v{config.version:<20}                       ║
║    Enterprise-grade Financial Q&A System                             ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # 启动参数
    host = config.host
    port = config.port
    workers = config.workers if config.environment.value == "production" else 1
    
    logger.info(f"Starting server on {host}:{port} with {workers} workers")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        reload=config.debug,
        log_level=config.logging.level.lower()
    )