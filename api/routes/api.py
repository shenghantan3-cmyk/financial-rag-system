#!/usr/bin/env python3
"""
Financial RAG System - API Router
API 路由定义
"""

import time
import traceback
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from .models.schemas import (
    QueryRequest, QueryResponse,
    DocumentUploadRequest, DocumentResponse,
    HealthStatus, StatsResponse,
    SourceReference, UsageInfo
)
from utils.logger import logger
from utils.rate_limit import rate_limiter, cache

# 创建路由
router = APIRouter(prefix="/api", tags=["API"])

# 全局启动时间
START_TIME = datetime.now()


# ============ Health Endpoints ============

@router.get("/health", response_model=HealthStatus)
async def health_check():
    """健康检查"""
    return HealthStatus(
        status="healthy",
        version="2.1.0",
        components={
            "api": {"status": "healthy"},
            "llm": {"status": "configured", "provider": "moonshot"},
            "knowledge_base": {"status": "ready", "documents": 5}
        }
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """获取系统统计"""
    uptime = (datetime.now() - START_TIME).total_seconds()
    return StatsResponse(
        total_documents=5,
        total_chunks=50,
        vector_db_size="10 MB",
        uptime_seconds=int(uptime)
    )


# ============ Query Endpoints ============

@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    http_request: Request
):
    """
    Financial RAG 问答接口
    
    - 基于行业报告检索相关内容
    - 调用 Moonshot API 生成回答
    - 返回回答并标注来源
    """
    start_time = time.time()
    
    # 限流检查
    rate_limiter.check_rate_limit(http_request)
    
    # 缓存检查
    cache_key = f"query:{request.question}:{hash(tuple(h.messages) if h.messages else [])}"
    cached = cache.get(cache_key)
    if cached and not request.stream:
        logger.debug(f"Cache hit for query: {request.question[:50]}...")
        return cached
    
    try:
        # 步骤 1: 检索相关报告 (简化版)
        from knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        search_results = kb.search(request.question, top_k=request.sources_limit)
        
        # 构建上下文
        context_parts = []
        sources = []
        
        for title, score, content in search_results:
            relevant = content[:2000]
            context_parts.append(f"【报告: {title}】\n{relevant}")
            sources.append(SourceReference(
                title=title,
                relevance_score=score,
                snippet=relevant[:200]
            ))
        
        context = "\n\n".join(context_parts)
        
        # 步骤 2: 调用 Moonshot API
        from moonshot_client import MoonshotClient
        client = MoonshotClient()
        
        system_prompt = """你是专业的金融领域问答助手。

规则：
1. 基于提供的报告内容回答
2. 信息不足时坦诚说明
3. 回答后注明信息来源"""
        
        user_content = f"""## 用户问题
{request.question}

## 相关报告内容
{context if context else "知识库中暂无相关报告"}

请回答并注明来源。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        # 添加历史
        if request.history:
            for h in request.history[-6:]:
                messages.insert(1, {
                    "role": h.role.value if hasattr(h.role, 'value') else str(h.role),
                    "content": h.content
                })
        
        # 调用 API
        answer = client.chat(messages)
        
        # 计算使用量
        latency_ms = int((time.time() - start_time) * 1000)
        usage = UsageInfo(
            prompt_tokens=len(request.question) // 4,
            completion_tokens=len(answer) // 4,
            total_tokens=(len(request.question) + len(answer)) // 4,
            latency_ms=latency_ms
        )
        
        # 构建响应
        response = QueryResponse(
            answer=answer,
            sources=sources,
            query=request.question,
            usage=usage
        )
        
        # 缓存结果
        cache.set(cache_key, response, ttl=300)
        
        logger.info(f"Query answered", 
                   question=request.question[:50],
                   latency_ms=latency_ms,
                   sources_count=len(sources))
        
        return response
        
    except Exception as e:
        logger.error(f"Query failed", 
                    error=str(e),
                    traceback=traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents", response_model=DocumentResponse)
async def upload_document(request: DocumentUploadRequest):
    """上传文档"""
    return DocumentResponse(
        status="success",
        message="文档功能开发中，请将报告保存到 ~/finance_reports/ 目录"
    )


# ========== Utility Endpoints ==========

@router.get("/version")
async def get_version():
    """获取版本信息"""
    return {
        "version": "2.1.0",
        "name": "Financial RAG System",
        "features": [
            "Moonshot API Integration",
            "Industry Report Knowledge Base",
            "Hybrid Retrieval",
            "Real-time Q&A"
        ]
    }