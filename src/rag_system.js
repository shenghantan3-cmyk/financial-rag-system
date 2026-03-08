/**
 * Financial RAG System - Main System
 * Integration of document processing, hybrid search, and graph-based reasoning
 */

import { HybridSearch } from './hybrid_search.js';
import { DocumentChunker } from './document_chunker.js';
import { createFinancialGraph } from './graph.js';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class FinancialRAGSystem {
  constructor(config = {}) {
    this.searcher = new HybridSearch({
      qdrantPath: config.qdrantPath || join(__dirname, '..', 'data', 'vector_db'),
      collectionName: config.collectionName || 'financial_reports'
    });
    
    this.chunker = new DocumentChunker({
      childChunkSize: config.chunkSize || 500,
      childChunkOverlap: config.chunkOverlap || 100,
      minParentSize: config.minParentSize || 2000,
      maxParentSize: config.maxParentSize || 4000
    });
    
    this.llm = null;
    this.graph = null;
    this.initialized = false;
  }
  
  /**
   * Initialize the RAG system
   */
  async initialize(llm) {
    if (this.initialized) return this;
    
    this.llm = llm;
    await this.searcher.initialize();
    
    this.graph = await createFinancialGraph({
      llm: this.llm,
      searcher: this.searcher
    });
    
    this.initialized = true;
    console.log('✅ Financial RAG System initialized');
    return this;
  }
  
  /**
   * Add documents to the knowledge base
   * @param {Array} documents - Array of {content, metadata: {source, url}}
   */
  async addDocuments(documents) {
    if (!this.initialized) {
      throw new Error('System not initialized. Call initialize() first.');
    }
    
    // Chunk documents
    const { parentChunks, childChunks } = await this.chunker.chunkDocuments(documents);
    
    console.log(`📦 Chunked into ${parentChunks.length} parent, ${childChunks.length} child chunks`);
    
    // Add child chunks to vector store (used for retrieval)
    await this.searcher.addDocuments(childChunks);
    
    // Store parent chunks separately for context retrieval
    await this._saveParentChunks(parentChunks);
    
    return { parentChunks: parentChunks.length, childChunks: childChunks.length };
  }
  
  /**
   * Save parent chunks to file storage
   */
  async _saveParentChunks(parents) {
    const parentDir = join(__dirname, '..', 'data', 'parent_store');
    const { mkdirSync, existsSync } = await import('fs');
    
    if (!existsSync(parentDir)) {
      mkdirSync(parentDir, { recursive: true });
    }
    
    const timestamp = Date.now();
    const filepath = join(parentDir, `parents_${timestamp}.json`);
    
    const parentData = parents.map(p => ({
      content: p.content,
      metadata: p.metadata
    }));
    
    const { writeFileSync } = await import('fs');
    writeFileSync(filepath, JSON.stringify(parentData, null, 2), 'utf-8');
    
    console.log(`💾 Saved ${parentData.length} parent chunks to ${filepath}`);
  }
  
  /**
   * Answer a question
   * @param {string} question - User question
   * @param {Object} options - Options
   */
  async ask(question, options = {}) {
    if (!this.initialized) {
      throw new Error('System not initialized. Call initialize() first.');
    }
    
    const { stream = false } = options;
    
    // For now, use the simple graph flow
    const state = {
      question,
      rewritten_query: '',
      sub_queries: [],
      retrieved_docs: [],
      context: '',
      answer: '',
      sources: [],
      chat_history: options.history || [],
      needs_clarification: false
    };
    
    // Step 1: Understand query
    const understood = await this.graph.nodes.understand(state);
    
    // Step 2: Rewrite query
    const rewritten = await this.graph.nodes.rewrite(understood);
    
    // Step 3: Retrieve
    const retrieved = await this.graph.nodes.retrieve(rewritten);
    
    // Step 4: Generate answer
    const answered = await this.graph.nodes.generate(retrieved);
    
    return {
      answer: answered.answer,
      sources: answered.sources,
      rewritten_query: answered.rewritten_query || rewritten.rewritten_query,
      retrieved_docs_count: answered.retrieved_docs.length
    };
  }
  
  /**
   * Get system stats
   */
  async getStats() {
    const vectorStats = await this.searcher.getStats();
    const { existsSync, readdirSync } = await import('fs');
    
    const parentDir = join(__dirname, '..', 'data', 'parent_store');
    const parentFiles = existsSync(parentDir) 
      ? readdirSync(parentDir).filter(f => f.endsWith('.json'))
      : [];
    
    return {
      vector_db: vectorStats,
      parent_chunks_files: parentFiles.length,
      initialized: this.initialized
    };
  }
  
  /**
   * Clear all data
   */
  async clear() {
    await this.searcher.clear();
    
    const { rmSync } = await import('fs');
    const parentDir = join(__dirname, '..', 'data', 'parent_store');
    
    try {
      rmSync(parentDir, { recursive: true, force: true });
    } catch (e) {}
    
    console.log('✅ System cleared');
  }
}

export default FinancialRAGSystem;