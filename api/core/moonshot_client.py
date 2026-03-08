#!/usr/bin/env python3
"""
Financial RAG System - Moonshot Client
Moonshot AI (Kimi) API 客户端
"""

import os
import json
import time
import urllib.request
import urllib.error
from typing import List, Dict, Optional


class MoonshotClient:
    """Moonshot AI API 客户端"""
    
    def __init__(
        self,
        api_key: str = None,
        api_base: str = "https://api.moonshot.cn/v1",
        model: str = "moonshot-v1-8k",
        timeout: int = 30,
        retry_times: int = 3
    ):
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        self.api_base = api_base
        self.model = model
        self.timeout = timeout
        self.retry_times = retry_times
        
        if not self.api_key:
            raise ValueError("Moonshot API key not configured")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> str:
        """
        发送对话请求
        
        Args:
            messages: 消息列表 [{role: "user", content: "..."}, ...]
            temperature: 温度 (0-1)
            max_tokens: 最大输出 token
            
        Returns:
            AI 回复文本
        """
        url = f"{self.api_base}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        data = json.dumps(payload).encode('utf-8')
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        last_error = None
        
        for attempt in range(self.retry_times):
            try:
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers=headers,
                    method='POST'
                )
                
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    
                    # 提取回答
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message'].get('content', '')
                        
                        # 计算使用量
                        usage = result.get('usage', {})
                        self._log_usage(usage, attempt)
                        
                        return content
                    else:
                        raise Exception(f"Unexpected response format: {result}")
                        
            except urllib.error.HTTPError as e:
                last_error = f"HTTP {e.code}: {e.read().decode('utf-8')}"
                if attempt < self.retry_times - 1:
                    time.sleep(1 * (attempt + 1))  # 指数退避
                    
            except Exception as e:
                last_error = str(e)
                if attempt < self.retry_times - 1:
                    time.sleep(1 * (attempt + 1))
        
        raise Exception(f"Moonshot API failed after {self.retry_times} attempts: {last_error}")
    
    def _log_usage(self, usage: Dict, attempt: int):
        """记录使用统计"""
        if usage:
            print(f"[Moonshot] Prompt: {usage.get('prompt_tokens', 0)}, "
                  f"Completion: {usage.get('completion_tokens', 0)}, "
                  f"Total: {usage.get('total_tokens', 0)}, "
                  f"Attempt: {attempt + 1}")
    
    def stream_chat(self, messages: List[Dict[str, str]]):
        """流式对话（暂不支持）"""
        raise NotImplementedError("Streaming not supported yet")


class MoonshotConfig:
    """Moonshot 配置"""
    
    AVAILABLE_MODELS = {
        "moonshot-v1-8k": {
            "name": "Moonshot V1 8K",
            "max_tokens": 8192,
            "description": "基础模型，适合简单任务"
        },
        "moonshot-v1-32k": {
            "name": "Moonshot V1 32K",
            "max_tokens": 32768,
            "description": "长上下文，适合复杂任务"
        },
        "moonshot-v1-128k": {
            "name": "Moonshot V1 128K",
            "max_tokens": 131072,
            "description": "超长上下文，适合长文档"
        }
    }
    
    @classmethod
    def get_model_info(cls, model_name: str) -> Dict:
        return cls.AVAILABLE_MODELS.get(model_name, {
            "name": model_name,
            "max_tokens": 8192,
            "description": "Unknown model"
        })


# 全局客户端
moonshot_client = MoonshotClient()