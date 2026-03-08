#!/usr/bin/env python3
"""
Financial RAG System - FastAPI Backend
基于 Moonshot API + 行业报告检索的金融问答系统
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "sk-u4t9cjHa85ZtmVkvcp5VHVosBbiiqE42IQXk94ExK2Bcih34")
MOONSHOT_API_BASE = "https://api.moonshot.cn/v1"
MOONSHOT_MODEL = "moonshot-v1-8k"

REPORTS_DIR = os.path.join(os.path.expanduser("~"), "finance_reports")


# ============================================================================
# Data Models
# ============================================================================

class QueryRequest(BaseModel):
    question: str
    history: Optional[List[Dict[str, str]]] = []
    stream: bool = False


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    query: str
    timestamp: str


class DocumentRequest(BaseModel):
    content: str
    metadata: Optional[Dict] = {}


class DocumentResponse(BaseModel):
    status: str
    chunks_added: Dict[str, int]


# ============================================================================
# Knowledge Base - 简单的基于关键词的检索
# ============================================================================

class KnowledgeBase:
    """简单基于关键词的行业报告知识库"""
    
    def __init__(self, reports_dir: str = REPORTS_DIR):
        self.reports_dir = reports_dir
        self.reports_cache = {}
        self.last_loaded = None
        
    def load_reports(self) -> Dict[str, Dict]:
        """加载所有报告到内存"""
        if not os.path.exists(self.reports_dir):
            return {}
            
        reports = {}
        date_dirs = [d for d in os.listdir(self.reports_dir) if os.path.isdir(os.path.join(self.reports_dir, d))]
        
        for date_dir in sorted(date_dirs, reverse=True):
            date_path = os.path.join(self.reports_dir, date_dir)
            for filename in os.listdir(date_path):
                if filename.endswith('.md'):
                    filepath = os.path.join(date_path, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            title = filename.replace('.md', '').replace('_', ' ')
                            reports[title] = {
                                'content': content,
                                'filepath': filepath,
                                'date': date_dir,
                                'title': title
                            }
                    except Exception as e:
                        print(f"加载报告失败 {filename}: {e}")
                        
        self.reports_cache = reports
        self.last_loaded = datetime.now()
        return reports
    
    def search(self, query: str, top_k: int = 3) -> List[Tuple[str, float, str]]:
        """关键词搜索"""
        if not self.reports_cache:
            self.load_reports()
            
        query_lower = query.lower()
        query_words = re.findall(r'\w+', query_lower)
        
        results = []
        for title, report in self.reports_cache.items():
            score = 0
            content = report['content']
            content_lower = content.lower()
            
            for word in query_words:
                if word in content_lower:
                    score += 1
                if word in title.lower():
                    score += 3
            
            if content:
                score = score / (len(content) / 1000 + 1)
                
            if score > 0:
                results.append((title, score, content))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


# ============================================================================
# Moonshot API Client
# ============================================================================

class MoonshotClient:
    """Moonshot AI (Kimi) API 客户端"""
    
    def __init__(self, api_key: str = MOONSHOT_API_KEY):
        self.api_key = api_key
        self.api_base = MOONSHOT_API_BASE
        self.model = MOONSHOT_MODEL
        
    def chat(self, messages: List[Dict[str, str]], system_prompt: str = None) -> str:
        """调用 Moonshot API"""
        import urllib.request
        import urllib.error
        
        url = f"{self.api_base}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3
        }
        
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            raise Exception(f"API 调用失败: {error_body}")
        except Exception as e:
            raise Exception(f"API 调用错误: {str(e)}")


# ============================================================================
# Global Instances
# ============================================================================

kb = KnowledgeBase()
moonshot = MoonshotClient()


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Financial RAG API",
    description="金融领域检索增强生成问答系统",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Serve the frontend UI"""
    import os
    api_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(api_dir)
    frontend_path = os.path.join(project_root, "ui", "index.html")
    
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return StreamingResponse(iter([f.read()]), media_type="text/html")
    return {"message": "Financial RAG API v2.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    stats = kb.load_reports()
    return {
        "status": "healthy",
        "version": "2.0.0",
        "moonshot": "configured" if MOONSHOT_API_KEY else "not configured",
        "reports": len(stats)
    }


@app.get("/stats")
async def get_stats():
    reports = kb.load_reports()
    return {"total_reports": len(kb.reports_cache), "model": MOONSHOT_MODEL}


@app.post("/api/query")
async def query(request: QueryRequest):
    """Financial RAG 问答核心接口"""
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    # Step 1: 检索相关报告
    search_results = kb.search(question, top_k=3)
    
    context_parts = []
    sources = []
    
    for title, score, content in search_results:
        relevant = content[:2000]
        context_parts.append(f"【报告: {title}】\n{relevant}")
        sources.append(title)
    
    context = "\n\n".join(context_parts)
    
    system_prompt = """你是专业的金融领域问答助手。

规则：
1. 基于提供的报告内容回答
2. 信息不足时坦诚说明
3. 回答后注明信息来源"""

    user_content = f"""## 用户问题
{question}

## 相关报告内容
{context if context else "知识库中暂无相关报告"}

请回答并注明来源。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    if request.history:
        for h in request.history[-6:]:
            messages.insert(1, {"role": h.get("role", "user"), "content": h.get("content", "")})
    
    try:
        answer = moonshot.chat(messages)
        
        sources_str = "\n\n**📚 参考来源：**\n" + "\n".join([f"- {s}" for s in sources]) if sources else ""
        full_answer = f"{answer}\n\n{sources_str}"
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            query=question,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        error_answer = f"""
抱歉，调用 AI 服务时遇到问题。

## 当前问题
{question}

## 错误信息
{str(e)}

## 相关报告摘要
{context[:500] if context else "暂无相关报告"}
"""
        
        return QueryResponse(
            answer=error_answer.strip(),
            sources=sources,
            query=question,
            timestamp=datetime.now().isoformat()
        )


@app.post("/api/documents")
async def add_document(request: DocumentRequest):
    return {"status": "success", "message": "请直接将报告保存到 ~/finance_reports/"}


# ============================================================================
# Run
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║    🏦 Financial RAG System v2.0                             ║
║    基于 Moonshot API + 行业报告智能问答                      ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    print("📚 加载行业报告...")
    kb.load_reports()
    print(f"✅ 已加载 {len(kb.reports_cache)} 份报告\n")
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)