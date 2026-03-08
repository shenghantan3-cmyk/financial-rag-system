#!/usr/bin/env python3
"""
Financial RAG System - Rate Limiter
企业级 API 限流器
"""

import time
import hashlib
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse


class RateLimiter:
    """滑动窗口限流器"""
    
    def __init__(self, requests_per_minute: int = 60, burst: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.windows: Dict[str, list] = {}
    
    def _get_key(self, request: Request) -> str:
        """获取请求唯一标识"""
        # 优先使用 API Key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{hashlib.md5(api_key.encode()).hexdigest()}"
        
        # 使用 IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _cleanup(self, key: str, window: int = 60):
        """清理过期请求"""
        now = time.time()
        if key in self.windows:
            self.windows[key] = [
                ts for ts in self.windows[key] 
                if now - ts < window
            ]
    
    def check_rate_limit(self, request: Request) -> Tuple[bool, int, int]:
        """
        检查是否超过限制
        
        Returns: (allowed, remaining, reset_time)
        """
        key = self._get_key(request)
        now = time.time()
        
        # 清理过期
        self._cleanup(key)
        
        # 获取当前窗口请求数
        if key not in self.windows:
            self.windows[key] = []
        
        request_count = len(self.windows[key])
        
        # 检查限制
        if request_count >= self.requests_per_minute:
            # 计算重置时间
            oldest = min(self.windows[key]) if self.windows[key] else now
            reset_time = int(oldest + 60 - now)
            return False, 0, max(0, reset_time)
        
        # 记录请求
        self.windows[key].append(now)
        
        remaining = self.requests_per_minute - request_count - 1
        return True, remaining, 60
    
    async def __call__(self, request: Request):
        """FastAPI 依赖"""
        allowed, remaining, reset_time = self.check_rate_limit(request)
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Too Many Requests",
                    "message": "请求过于频繁，请稍后再试",
                    "retry_after": reset_time
                },
                headers={
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time)
                }
            )


class InMemoryCache:
    """内存缓存"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache: Dict[str, tuple] = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def _generate_key(self, key: str) -> str:
        return f"cache:{hashlib.md5(key.encode()).hexdigest()}"
    
    def get(self, key: str) -> Optional[any]:
        """获取缓存"""
        full_key = self._generate_key(key)
        now = time.time()
        
        if full_key in self.cache:
            value, expires = self.cache[full_key]
            if now < expires:
                return value
            del self.cache[full_key]
        
        return None
    
    def set(self, key: str, value: any, ttl: int = None):
        """设置缓存"""
        full_key = self._generate_key(key)
        ttl = ttl or self.ttl
        
        # 清理过期
        now = time.time()
        expired = [k for k, v in self.cache.items() if v[1] < now]
        for k in expired:
            del self.cache[k]
        
        # LRU 清理
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache.items(), key=lambda x: x[1][1])
            del self.cache[oldest[0]]
        
        self.cache[full_key] = (value, now + ttl)
    
    def delete(self, key: str):
        """删除缓存"""
        full_key = self._generate_key(key)
        if full_key in self.cache:
            del self.cache[full_key]


# 全局实例
rate_limiter = RateLimiter(requests_per_minute=60, burst=10)
cache = InMemoryCache(max_size=1000, ttl=3600)