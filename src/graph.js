/**
 * Financial RAG Graph - LangGraph Implementation
 * 
 * Graph Flow:
 * understand_query → rewrite_query → clarify_query → 
 * parallel_retrieve ← aggregate_responses → generate_answer
 */

import { createInitialState, addRetrievalResults, setFinalAnswer } from './graph_state.js';
import { HybridSearch } from './hybrid_search.js';

export const FinancialGraphState = {
  question: 'string',
  rewritten_query: 'string',
  sub_queries: 'list',
  retrieved_docs: 'list',
  context: 'string',
  answer: 'string',
  sources: 'list',
  needs_clarification: 'boolean',
  clarification_question: 'string'
};

/**
 * Node: Understand and summarize conversation
 */
export async function understandQuery(state) {
  // Analyze chat history to extract context
  const history = state.chat_history || [];
  const summary = history.length > 0 
    ? history.map(h => `${h.role}: ${h.content.substring(0, 100)}...`).join('\n')
    : '';
  
  return {
    ...state,
    summary
  };
}

/**
 * Node: Rewrite and clarify query
 */
export async function rewriteQuery(state, llm, prompt) {
  const query = state.question;
  
  // Build context from history
  const historyContext = state.summary 
    ? `\nConversation history:\n${state.summary}` 
    : '';
  
  const fullPrompt = prompt || `You are a financial query rewriter. 

Current query: "${query}"
${historyContext}

Task: Rewrite this query to be more precise for document retrieval.

Output JSON format:
{
  "rewritten_query": "improved query or original if already good",
  "needs_clarification": false/true,
  "clarification_question": "question to ask if unclear",
  "sub_queries": ["sub-query 1", "sub-query 2"]
}

Example:
- "它怎么投资" → "How to invest in AI industry"
- "2026年AI怎么样？" → "AI industry outlook 2026"
- "What about the risks and rewards?" → ["investment risks", "investment rewards"]`;

  try {
    const response = await llm.invoke(fullPrompt);
    const parsed = JSON.parse(response.content || '{}');
    
    return {
      ...state,
      rewritten_query: parsed.rewritten_query || query,
      sub_queries: parsed.sub_queries || (parsed.needs_clarification ? [] : [query]),
      needs_clarification: parsed.needs_clarification || false,
      clarification_question: parsed.clarification_question || ''
    };
  } catch (error) {
    // On error, use original query
    return {
      ...state,
      rewritten_query: query,
      sub_queries: [query],
      needs_clarification: false
    };
  }
}

/**
 * Node: Retrieve documents using hybrid search
 */
export async function retrieveDocuments(state, searcher) {
  const queries = state.sub_queries.length > 0 ? state.sub_queries : [state.question];
  let allDocs = [];
  const seen = new Set();
  
  for (const query of queries) {
    try {
      const docs = await searcher.search(query, { limit: 10 });
      
      for (const doc of docs) {
        const key = doc.content?.substring(0, 100) || doc.url;
        if (!seen.has(key)) {
          seen.add(key);
          allDocs.push(doc);
        }
      }
    } catch (error) {
      console.error('Search error:', error.message);
    }
  }
  
  return addRetrievalResults(state, allDocs);
}

/**
 * Node: Generate final answer
 */
export async function generateAnswer(state, llm, prompt) {
  const docsContent = state.retrieved_docs
    .map(d => d.content || '')
    .join('\n\n---\n\n');
  
  const sources = state.retrieved_docs
    .map(d => d.metadata?.source || d.url || 'Unknown')
    .filter((v, i, a) => a.indexOf(v) === i)
    .join('\n');
  
  const fullPrompt = prompt || `You are a financial domain Q&A assistant.

User Question: ${state.question}

Context from knowledge base:
${docsContent}

${sources ? `Sources:\n${sources}` : ''}

Please answer the question based ONLY on the above context. 
If the context doesn't contain enough information, say so clearly.
Keep your answer professional and accurate.`;  try {
    const response = await llm.invoke(fullPrompt);
    
    const answer = typeof response === 'string' 
      ? response 
      : response.content || '';
    
    return setFinalAnswer(state, answer);
  } catch (error) {
    return {
      ...state,
      answer: `Error generating answer: ${error.message}`
    };
  }
}

/**
 * Edge: Route based on query complexity
 */
export function shouldParallelRetrieve(state) {
  // If multiple sub-queries, use parallel retrieval
  if (state.sub_queries.length > 1) {
    return 'parallel_retrieve';
  }
  // Otherwise, single retrieval
  return 'single_retrieve';
}

/**
 * Edge: Route after clarification
 */
export function shouldClarify(state) {
  if (state.needs_clarification) {
    return 'clarify';
  }
  return 'retrieve';
}

/**
 * Edge: Route after retrieval
 */
export function shouldGenerate(state) {
  if (state.retrieved_docs.length === 0) {
    // No documents found, generate answer with what we have
    return 'generate_empty';
  }
  return 'generate';
}

/**
 * Build the Financial RAG Graph
 */
export async function createFinancialGraph(config = {}) {
  const {
    llm,
    searcher = new HybridSearch(config.search),
    prompt = null
  } = config;
  
  // Graph structure will be built with LangGraph
  // This is a placeholder for the structure definition
  
  const graph = {
    nodes: {
      understand: understandQuery,
      rewrite: (state) => rewriteQuery(state, llm, prompt),
      retrieve: (state) => retrieveDocuments(state, searcher),
      generate: (state) => generateAnswer(state, llm, prompt)
    },
    edges: [
      { from: 'understand', to: 'rewrite' },
      { from: 'rewrite', to: 'retrieve' },
      { from: 'retrieve', to: 'generate' }
    ],
    start: 'understand',
    end: 'generate'
  };
  
  console.log('✅ Financial RAG Graph created');
  return graph;
}

export default {
  FinancialGraphState,
  createFinancialGraph,
  understandQuery,
  rewriteQuery,
  retrieveDocuments,
  generateAnswer,
  shouldParallelRetrieve,
  shouldClarify,
  shouldGenerate
};