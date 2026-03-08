#!/usr/bin/env node
/**
 * Financial RAG System - Main Entry Point
 * 
 * Architecture:
 * ┌─────────────────────────────────────────────────────────┐
 * │                    Gradio Web UI                        │
 │    (Chat interface + Document Upload)                    │
 └────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 Financial RAG Agent                      │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Conversation Memory (stateful)                 │    │
│  │  - Chat history                                 │    │
│  │  - Summary of previous questions                │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                                │
│                          ▼                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Query Understanding Node                        │    │
│  │  - Rewrite ambiguous queries                    │    │
│  │  - Detect references ("it", "that")             │    │
│  │  - Split multi-part questions                   │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                                │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Parallel Agent Retrieval                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ Agent 1  │  │ Agent 2  │  │ Agent 3  │  ...          │
│  │ (sub-q1) │  │ (sub-q2) │  │ (sub-q3) │               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
│       │             │             │                       │
│       ▼             ▼             ▼                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Hybrid Search (Qdrant)                          │    │
│  │  - Dense: sentence-transformers (all-mpnet)      │    │
│  │  - Sparse: BM25 for keyword matching             │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                                │
│                          ▼                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Response Aggregation                            │    │
│  │  - Combine all agent responses                  │    │
│  │  - Generate final coherent answer               │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Document Knowledge Base                     │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Parent/Child Chunking Strategy                  │    │
│  │  - Parent: Large sections (H1/H2 headers)       │    │
│  │  - Child: Small chunks (500 tokens, 100 overlap)│    │
│  └─────────────────────────────────────────────────┘    │
│                          │                                │
│                          ▼                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Qdrant Vector Database                          │    │
│  │  - Dense + Sparse (BM25) hybrid retrieval       │    │
│  │  - Parent store for context retrieval           │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
*/

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Version and metadata
export const VERSION = '1.0.0';
export const PROJECT_NAME = 'Financial RAG System';

export const CONFIG = {
  // Paths
  DATA_DIR: join(__dirname, '..', 'data'),
  DOCS_DIR: join(__dirname, '..', 'docs'),
  MARKDOWN_DIR: join(__dirname, '..', 'markdown'),
  
  // Vector Database
  QDRANT_PATH: join(__dirname, '..', 'data', 'vector_db'),
  COLLECTION_NAME: 'financial_reports_chunks',
  
  // Embedding Models
  DENSE_MODEL: 'sentence-transformers/all-mpnet-base-v2',
  
  // Chunking
  CHILD_CHUNK_SIZE: 500,
  CHILD_CHUNK_OVERLAP: 100,
  MIN_PARENT_SIZE: 2000,
  MAX_PARENT_SIZE: 4000,
  
  // Agent
  MAX_TOOL_CALLS: 8,
  MAX_ITERATIONS: 10,
  BASE_TOKEN_THRESHOLD: 2000,
  
  // LLM
  LLM_MODEL: 'qwen3:4b-instruct-2507-q4_K_M',
  LLM_TEMPERATURE: 0
};

// Default system prompt for financial Q&A
export const DEFAULT_PROMPT = `你是专业的金融领域问答助手。

任务是基于提供的金融研究报告和公开信息，回答用户的问题。

## 工作流程：
1. 分析用户问题，提取关键概念
2. 在知识库中检索相关信息
3. 基于检索结果生成准确、专业的回答
4. 如有必要，标注信息来源

## 回答原则：
- 准确性：只基于检索到的信息回答，不编造
- 专业性：使用金融专业术语
- 完整性：覆盖问题的多个方面
- 溯源性：注明信息来源

## 回复格式：
1. 直接回答问题
2. 如有数据，提供具体数值和日期
3. 列出主要参考来源
4. 如信息不足，坦诚说明`;

// Component exports
export { FinancialRAGSystem } from './rag_system.js';
export { DocumentManager } from './document_manager.js';
export { HybridSearch } from './hybrid_search.js';
export { createFinancialGraph, FinancialGraphState } from './graph.js';

console.log(`✅ ${PROJECT_NAME} v${VERSION} loaded`);
console.log(`📁 Data directory: ${CONFIG.DATA_DIR}`);
console.log(`🗃️  Vector DB: ${CONFIG.QDRANT_PATH}`);