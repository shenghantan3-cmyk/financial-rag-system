/**
 * Document Chunker - Parent/Child Strategy
 * 
 * Based on agentic-rag-for-dummies implementation
 * Splits documents into:
 * - Parent chunks: Large sections based on Markdown headers (H1, H2, H3)
 * - Child chunks: Small, fixed-size pieces (500 tokens, 100 overlap)
 */

import { RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter } from '@langchain/text_splitters';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class DocumentChunker {
  constructor(config = {}) {
    this.childChunkSize = config.childChunkSize || 500;
    this.childChunkOverlap = config.childChunkOverlap || 100;
    this.minParentSize = config.minParentSize || 2000;
    this.maxParentSize = config.maxParentSize || 4000;
    
    this.headersToSplitOn = config.headersToSplitOn || [
      ['#', 'H1'],
      ['##', 'H2'],
      ['###', 'H3']
    ];
  }
  
  /**
   * Split documents into parent/child chunks
   * @param {Array} documents - Array of {content, metadata, source}
   * @returns {Object} { parentChunks, childChunks }
   */
  async chunkDocuments(documents) {
    const parentChunks = [];
    const childChunks = [];
    
    for (const doc of documents) {
      // Skip empty documents
      if (!doc.content || doc.content.trim().length === 0) continue;
      
      // Step 1: Split into parent chunks by headers
      const parents = await this._chunkIntoParents(doc);
      
      // Step 2: Split parents into child chunks
      const children = await this._chunkIntoChildren(parents);
      
      // Store chunks
      for (const parent of parents) {
        parentChunks.push({
          content: parent.pageContent,
          metadata: {
            ...parent.metadata,
            source: doc.metadata?.source || 'unknown',
            chunk_type: 'parent'
          }
        });
      }
      
      for (const child of children) {
        childChunks.push({
          content: child.pageContent,
          metadata: {
            ...child.metadata,
            source: doc.metadata?.source || 'unknown',
            chunk_type: 'child',
            parent_index: child.metadata.parent_index
          }
        });
      }
    }
    
    return { parentChunks, childChunks };
  }
  
  /**
   * Split document into parent chunks by Markdown headers
   */
  async _chunkIntoParents(doc) {
    const parentSplitter = new MarkdownHeaderTextSplitter({
      headersToSplitOn: this.headersToSplitOn,
      stripHeaders: false
    });
    
    const splits = await parentSplitter.splitText(doc.content);
    
    // Merge small splits and clean metadata
    const merged = [];
    for (const split of splits) {
      // Clean and merge metadata
      const cleaned = { ...split.metadata };
      
      merged.push({
        pageContent: split.pageContent,
        metadata: {
          ...cleaned,
          source_file: doc.metadata?.source || 'unknown',
          chunk_type: 'parent'
        }
      });
    }
    
    // Merge small parents, split large parents
    const processed = this._processParents(merged);
    
    return processed;
  }
  
  /**
   * Process parent chunks: merge small, split large
   */
  _processParents(chunks) {
    if (chunks.length === 0) return [];
    
    const merged = this._mergeSmallParents(chunks);
    const final = this._splitLargeParents(merged);
    
    return final;
  }
  
  /**
   * Merge small parent chunks
   */
  _mergeSmallParents(chunks) {
    if (!chunks || chunks.length === 0) return [];
    
    const merged = [];
    let current = null;
    
    for (const chunk of chunks) {
      if (current === null) {
        current = { ...chunk };
      } else {
        // Merge content
        current.pageContent += '\n\n' + chunk.pageContent;
        
        // Merge metadata
        for (const [key, value] of Object.entries(chunk.metadata)) {
          if (key in current.metadata) {
            current.metadata[key] = `${current.metadata[key]} -> ${value}`;
          } else {
            current.metadata[key] = value;
          }
        }
      }
      
      // Check if current is big enough
      if (current.pageContent.length >= this.minParentSize) {
        merged.push(current);
        current = null;
      }
    }
    
    // Handle remaining
    if (current) {
      if (merged.length > 0) {
        merged[merged.length - 1].pageContent += '\n\n' + current.pageContent;
        // Update merged[-1] metadata reference for children
      } else {
        merged.push(current);
      }
    }
    
    return merged;
  }
  
  /**
   * Split large parent chunks
   */
  _splitLargeParents(chunks) {
    const splitter = new RecursiveCharacterTextSplitter({
      chunk_size: this.maxParentSize,
      chunk_overlap: 0
    });
    
    const splitChunks = [];
    
    for (const chunk of chunks) {
      if (chunk.pageContent.length <= this.maxParentSize) {
        splitChunks.push(chunk);
      } else {
        const subChunks = splitter.splitDocuments([chunk]);
        for (const sub of subChunks) {
          splitChunks.push({
            pageContent: sub.pageContent,
            metadata: {
              ...chunk.metadata,
              // Keep parent metadata
              original_size: chunk.pageContent.length,
              chunk_type: 'parent_split'
            }
          });
        }
      }
    }
    
    return splitChunks;
  }
  
  /**
   * Split parent chunks into child chunks
   */
  async _chunkIntoChildren(parents) {
    const childSplitter = new RecursiveCharacterTextSplitter({
      chunk_size: this.childChunkSize,
      chunk_overlap: this.childChunkOverlap
    });
    
    const children = [];
    
    for (let i = 0; i < parents.length; i++) {
      const parent = parents[i];
      const subChunks = await childSplitter.splitText(parent.pageContent);
      
      for (const content of subChunks) {
        children.push({
          pageContent: content,
          metadata: {
            ...parent.metadata,
            parent_index: i,
            chunk_type: 'child'
          }
        });
      }
    }
    
    return children;
  }
  
  /**
   * Clean parent store (for small child chunks that could merge)
   */
  cleanParentStore(parents, minSize = 500) {
    const cleaned = [];
    
    for (let i = 0; i < parents.length; i++) {
      const current = parents[i];
      
      if (current.pageContent.length < minSize) {
        if (cleaned.length > 0) {
          // Append to previous
          cleaned[cleaned.length - 1].pageContent += '\n\n' + current.pageContent;
          
          // Merge metadata
          for (const [key, value] of Object.entries(current.metadata)) {
            if (key in cleaned[cleaned.length - 1].metadata) {
              cleaned[cleaned.length - 1].metadata[key] = 
                `${value} -> ${cleaned[cleaned.length - 1].metadata[key]}`;
            } else {
              cleaned[cleaned.length - 1].metadata[key] = value;
            }
          }
        }
      } else {
        cleaned.push(current);
      }
    }
    
    return cleaned;
  }
}

export default DocumentChunker;