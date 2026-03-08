#!/usr/bin/env python3
"""
Financial RAG System - API Models
API 数据模型定义
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SourceType(str, Enum):
    REPORT = "report"
    KNOWLEDGE_BASE = "knowledge_base"
    WEB = "web"


# ============ Request Models ============

class ChatMessage(BaseModel):
    """对话消息"""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None


class QueryRequest(BaseModel):
    """问答请求"""
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    history: Optional[List[ChatMessage]] = Field(default=[], description="对话历史")
    stream: bool = Field(default=False, description="是否流式输出")
    temperature: Optional[float] = Field(default=None, ge=0, le=1, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, ge=100, le=8192, description="最大输出token")
    sources_limit: Optional[int] = Field(default=5, ge=1, ge=20, description="最大参考文档数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "2026年人工智能行业趋势如何？",
                "history": [
                    {"role": "user", "content": "请分析AI行业"}
                ],
                "stream": False
            }
        }


class DocumentUploadRequest(BaseModel):
    """文档上传请求"""
    content: str = Field(..., description="文档内容")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="元数据")


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: Optional[Dict[str, str]] = None


# ============ Response Models ============

class SourceReference(BaseModel):
    """来源引用"""
    title: str = Field(..., description="文档标题")
    url: Optional[str] = Field(default=None, description="来源链接")
    relevance_score: float = Field(default=0.0, ge=0, le=1, description="相关性分数")
    snippet: Optional[str] = Field(default=None, description="相关内容片段")


class UsageInfo(BaseModel):
    """API 使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0


class QueryResponse(BaseModel):
    """问答响应"""
    answer: str = Field(..., description="AI 回答")
    sources: List[SourceReference] = Field(default=[], description="参考来源")
    query: str = Field(..., description="原始问题")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    usage: Optional[UsageInfo] = Field(default=None, description="使用统计")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "根据行业报告，2026年AI行业...",
                "sources": [
                    {
                        "title": "2026年人工智能趋势报告",
                        "url": "https://...",
                        "relevance_score": 0.95
                    }
                ],
                "query": "2026年人工智能行业趋势如何？",
                "timestamp": "2026-03-08T16:30:00"
            }
        }


class DocumentResponse(BaseModel):
    """文档操作响应"""
    status: str = Field(..., description="状态")
    document_id: Optional[str] = Field(default=None, description="文档ID")
    chunks_created: int = Field(default=0, description="创建的块数")
    message: str = Field(default="")


class SearchResponse(BaseModel):
    """搜索响应"""
    results: List[Dict[str, Any]] = Field(default=[])
    total_found: int = Field(default=0)
    query: str = Field(...)


# ============ System Models ============

class HealthStatus(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="整体状态")
    version: str = Field(..., description="版本号")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: Dict[str, Dict[str, Any]] = Field(default={}, description="组件状态")


class StatsResponse(BaseModel):
    """统计信息响应"""
    total_documents: int = Field(default=0)
    total_chunks: int = Field(default=0)
    vector_db_size: str = Field(default="0 MB")
    last_updated: Optional[datetime] = None
    uptime_seconds: int = Field(default=0)


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误信息")
    code: int = Field(default=500, description="错误码")
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)