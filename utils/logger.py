#!/usr/bin/env python3
"""
Financial RAG System - Logger
日志系统
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """简化日志器"""
    
    def __init__(self, name: str = "financial-rag", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))
        self.logger.handlers = []
        
        # 控制台
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
        console.setFormatter(fmt)
        self.logger.addHandler(console)
        
        # 文件
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"app_{datetime.now().strftime('%Y-%m-%d')}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        self.logger.addHandler(file_handler)
    
    def debug(self, msg: str):
        self.logger.debug(msg)
    
    def info(self, msg: str):
        self.logger.info(msg)
    
    def warning(self, msg: str):
        self.logger.warning(msg)
    
    def error(self, msg: str, exc: Exception = None):
        self.logger.error(msg)
        if exc:
            self.logger.exception(str(exc))
    
    def critical(self, msg: str):
        self.logger.critical(msg)


# 全局日志器
logger = Logger()


def get_logger(name: str = None) -> Logger:
    """获取日志器"""
    if name:
        return Logger(name)
    return logger