#!/usr/bin/env python3
"""
Financial RAG System - Enterprise Configuration
企业级配置管理
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
import os


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseModel):
    """数据库配置"""
    provider: str = "qdrant"
    path: str = "./data/vector_db"
    collection_name: str = "financial_reports"
    sparse_vector_name: str = "sparse"
    embedding_dim: int = 768
    enable_hybrid_search: bool = True


class LLMCConfig(BaseModel):
    """LLM 配置"""
    provider: str = "moonshot"  # moonshot, openai, anthropic, ollama
    api_key: Optional[str] = None
    api_base: str = "https://api.moonshot.cn/v1"
    model: str = "moonshot-v1-8k"
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout: int = 30
    retry_times: int = 3


class CacheConfig(BaseModel):
    """缓存配置"""
    enabled: bool = True
    type: str = "memory"  # memory, redis
    ttl: int = 3600  # 秒
    max_size: int = 1000


class RateLimitConfig(BaseModel):
    """限流配置"""
    enabled: bool = True
    requests_per_minute: int = 60
    burst: int = 10


class SecurityConfig(BaseModel):
    """安全配置"""
    cors_origins: List[str] = ["*"]
    api_key_header: str = "X-API-Key"
    allowed_api_keys: List[str] = []
    enable_rate_limit: bool = True


class LoggingConfig(BaseModel):
    """日志配置"""
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "./logs/app.log"
    max_size: str = "100M"
    backup_count: int = 5
    enable_console: bool = True


class AppConfig(BaseModel):
    """应用主配置"""
    name: str = "Financial RAG System"
    version: str = "2.0.0"
    environment: Environment = Environment.PRODUCTION
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 1
    
    # 子配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMCConfig = Field(default_factory=LLMCConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # 知识库
    reports_dir: str = "./finance_reports"
    max_context_length: int = 4000
    max_source_docs: int = 5
    
    class Config:
        extra = "ignore"


def load_config(config_path: str = None) -> AppConfig:
    """加载配置"""
    import json
    import yaml
    
    config = AppConfig()
    
    # 优先从环境变量加载
    if os.getenv("APP_ENV"):
        config.environment = Environment(os.getenv("APP_ENV"))
    
    if os.getenv("APP_PORT"):
        config.port = int(os.getenv("APP_PORT"))
    
    if os.getenv("MOONSHOT_API_KEY"):
        config.llm.api_key = os.getenv("MOONSHOT_API_KEY")
    
    if os.getenv("REPORTS_DIR"):
        config.reports_dir = os.getenv("REPORTS_DIR")
    
    if os.getenv("LOG_LEVEL"):
        config.logging.level = LogLevel(os.getenv("LOG_LEVEL"))
    
    return config


# 全局配置实例
config = load_config()