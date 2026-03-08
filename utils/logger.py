#!/usr/bin/env python3
"""
Financial RAG System - Enterprise Logger
企业级日志系统
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from functools import wraps
import json


class JSONFormatter(logging.Formatter):
    """JSON 格式日志"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra_data'):
            log_obj.update(record.extra_data)
        
        return json.dumps(log_obj, ensure_ascii=False)


class EnterpriseLogger:
    """企业级日志器"""
    
    def __init__(self, name: str = "financial-rag"):
        self.logger = logging.getLogger(name)
        self.setup()
    
    def setup(self, level: str = "INFO", log_path: str = "./logs"):
        """设置日志器"""
        self.logger.setLevel(getattr(logging, level))
        
        # 清除现有处理器
        self.logger.handlers = []
        
        # 创建 logs 目录
        Path(log_path).mkdir(parents=True, exist_ok=True)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器 - 按天滚动
        log_file = Path(log_path) / f"app_{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # JSON 错误日志（用于监控）
        error_file = Path(log_path) / "errors.json.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(error_handler)
    
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, extra_data=kwargs)
    
    def info(self, msg: str, **kwargs):
        self.logger.info(msg, extra_data=kwargs)
    
    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, extra_data=kwargs)
    
    def error(self, msg: str, exc: Exception = None, **kwargs):
        self.logger.error(msg, extra_data=kwargs)
        if exc:
            self.logger.exception(str(exc))
    
    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, extra_data=kwargs)
    
    def metric(self, name: str, value: float, tags: dict = None):
        """发送指标（用于监控）"""
        self.logger.info(f"METRIC: {name}={value}", extra_data={
            "type": "metric",
            "name": name,
            "value": value,
            "tags": tags or {}
        })
    
    def trace_function(self, func):
        """函数追踪装饰器"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.debug(f"Entering {func.__name__}", function=func.__name__)
            start = datetime.now()
            result = func(*args, **kwargs)
            duration = (datetime.now() - start).total_seconds()
            self.debug(f"Exiting {func.__name__}", 
                      function=func.__name__, 
                      duration_ms=duration * 1000)
            return result
        return wrapper


# 全局日志器实例
logger = EnterpriseLogger()


def get_logger(name: str = None) -> EnterpriseLogger:
    """获取日志器"""
    if name:
        return EnterpriseLogger(name)
    return logger