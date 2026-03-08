#!/usr/bin/env python3
"""
Financial RAG System - Knowledge Base
行业报告知识库
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class KnowledgeBase:
    """行业报告知识库"""
    
    def __init__(self, reports_dir: str = None):
        self.reports_dir = reports_dir or os.path.join(
            os.path.expanduser("~"), 
            "finance_reports"
        )
        self.reports_cache: Dict[str, Dict] = {}
        self.last_loaded: Optional[datetime] = None
        self._load_reports()
    
    def _load_reports(self):
        """加载所有报告到内存"""
        if not os.path.exists(self.reports_dir):
            return {}
        
        reports = {}
        date_dirs = sorted(
            [d for d in os.listdir(self.reports_dir) 
             if os.path.isdir(os.path.join(self.reports_dir, d))],
            reverse=True
        )
        
        for date_dir in date_dirs:
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
                            'title': title,
                            'word_count': len(content)
                        }
                    except Exception as e:
                        print(f"加载报告失败 {filename}: {e}")
        
        self.reports_cache = reports
        self.last_loaded = datetime.now()
        print(f"✅ 已加载 {len(reports)} 份行业报告")
        return reports
    
    def reload(self):
        """重新加载报告"""
        self.reports_cache = {}
        return self._load_reports()
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        min_score: float = 0.01
    ) -> List[Tuple[str, float, str]]:
        """
        关键词搜索
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            min_score: 最低分数阈值
            
        Returns:
            [(title, score, content), ...]
        """
        if not self.reports_cache:
            self._load_reports()
        
        query_lower = query.lower()
        query_words = re.findall(r'\w+', query_lower)
        
        results = []
        
        for title, report in self.reports_cache.items():
            score = 0.0
            content = report['content']
            content_lower = content.lower()
            
            # 1. 标题匹配 (高权重)
            title_lower = title.lower()
            for word in query_words:
                if word in title_lower:
                    score += 3.0  # 标题加 3 分
            
            # 2. 内容关键词匹配
            for word in query_words:
                if word in content_lower:
                    # 出现次数
                    count = content_lower.count(word)
                    score += min(count * 0.5, 5.0)  # 最多加 5 分
            
            # 3. 分词匹配
            search_words = set(query_words)
            content_words = set(re.findall(r'\w+', content_lower))
            overlap = search_words & content_words
            score += len(overlap) * 0.3  # 每个重叠词加 0.3 分
            
            # 4. 长度归一化
            word_count = report.get('word_count', len(content))
            if word_count > 0:
                score = score / (word_count / 1000 + 1)
            
            # 5. 金融领域关键词加权
            finance_keywords = ['行业', '市场', '投资', '估值', '增长率', '营收', '利润', 'AI', '人工智能', '新能源', '半导体']
            for keyword in finance_keywords:
                if keyword in content_lower:
                    score *= 1.1  # 增加 10%
            
            if score >= min_score:
                results.append((title, score, content[:2500]))
        
        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def get_document(self, title: str) -> Optional[Dict]:
        """获取指定文档"""
        for t, doc in self.reports_cache.items():
            if title.lower() in t.lower():
                return doc
        return None
    
    def get_all_documents(self) -> List[Dict]:
        """获取所有文档"""
        return list(self.reports_cache.values())
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_words = sum(
            doc.get('word_count', 0) 
            for doc in self.reports_cache.values()
        )
        
        return {
            "total_documents": len(self.reports_cache),
            "total_words": total_words,
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None,
            "reports_dir": self.reports_dir
        }


# 全局实例
knowledge_base = KnowledgeBase()