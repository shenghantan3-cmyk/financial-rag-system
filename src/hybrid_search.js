/**
 * Financial RAG System - Hybrid Search
 * Combines dense (embedding) + sparse (BM25) retrieval from Qdrant
 */

import { QdrantVectorStore } from '@langchain/qdrant';
import { HuggingFaceEmbeddings } from '@langchain/huggingface';
import { QdrantSparseEmbeddings } from '@langchain/qdrant';
import { QdrantClient } from '@qdrant/qdrant-js';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class HybridSearch {
  constructor(config = {}) {
    this.qdrantPath = config.qdrantPath || join(__dirname, '..', '..', 'data', 'vector_db');
    this.collectionName = config.collectionName || 'financial_reports';
    this.denseModel = config.denseModel || 'sentence-transformers/all-mpnet-base-v2';
    
    this.client = new QdrantClient({ path: this.qdrantPath });
    this.vectorStore = null;
    this.denseEmbeddings = null;
    this.sparseEmbeddings = null;
  }
  
  /**
   * Initialize the hybrid search system
   */
  async initialize() {
    const embeddingDimension = 768; // all-mpnet-base-v2 dimension
    
    // Ensure collection exists
    const collections = await this.client.getCollections();
    const exists = collections.collections.some(c => c.name === this.collectionName);
    
    if (!exists) {
      await this.client.createCollection({
        collection_name: this.collectionName,
        vectors_config: {
          size: embeddingDimension,
          distance: 'COSINE'
        },
        sparse_vectors_config: {
          sparse: {}
        }
      });
      console.log(`✅ Created collection: ${this.collectionName}`);
    }
    
    // Initialize embeddings
    this.denseEmbeddings = new HuggingFaceEmbeddings({
      modelName: this.denseModel
    });
    
    this.sparseEmbeddings = new QdrantSparseEmbeddings({
      modelName: 'Qdrant/bm25',
      onLoadCompleted: () => console.log('✅ BM25 sparse embeddings loaded')
    });
    
    // Initialize vector store
    this.vectorStore = await QdrantVectorStore.fromExistingCollection(
      this.denseEmbeddings,
      {
        client: this.client,
        collectionName: this.collectionName,
        sparseEmbedding: this.sparseEmbeddings
      }
    );
    
    console.log('✅ Hybrid search initialized');
    return this;
  }
  
  /**
   * Search with query
   * @param {string} query - Search query
   * @param {Object} options - Search options
   */
  async search(query, options = {}) {
    if (!this.vectorStore) {
      await this.initialize();
    }
    
    const { limit = 10, filters = {} } = options;
    
    try {
      // Hybrid search results
      const results = await this.vectorStore.similaritySearch(
        query,
        limit,
        filters
      );
      
      return results.map(doc => ({
        content: doc.pageContent,
        metadata: doc.metadata,
        score: doc.metadata?.score || 0
      }));
    } catch (error) {
      console.error('Search error:', error.message);
      return [];
    }
  }
  
  /**
   * Add documents to the knowledge base
   * @param {Array} documents - Array of document objects
   */
  async addDocuments(documents) {
    if (!this.vectorStore) {
      await this.initialize();
    }
    
    const docs = documents.map(doc => ({
      pageContent: doc.content,
      metadata: {
        ...doc.metadata,
        source: doc.source,
        date_added: new Date().toISOString()
      }
    }));
    
    await this.vectorStore.addDocuments(docs);
    console.log(`✅ Added ${docs.length} documents to vector store`);
    
    return docs.length;
  }
  
  /**
   * Get collection info
   */
  async getStats() {
    try {
      const collection = await this.client.getCollection(this.collectionName);
      return {
        name: this.collectionName,
        vectors_count: collection.vectors_count,
        status: collection.status
      };
    } catch (error) {
      return { error: error.message };
    }
  }
  
  /**
   * Clear the collection
   */
  async clear() {
    try {
      const collections = await this.client.getCollections();
      const exists = collections.collections.some(c => c.name === this.collectionName);
      
      if (exists) {
        await this.client.deleteCollection(this.collectionName);
        console.log(`✅ Cleared collection: ${this.collectionName}`);
      }
    } catch (error) {
      console.error('Clear error:', error.message);
    }
  }
}

export default HybridSearch;