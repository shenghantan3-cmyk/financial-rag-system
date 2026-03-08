/**
 * Financial RAG Graph State
 * Defines the state schema for LangGraph nodes
 */

export const INITIAL_STATE = {
  // User input
  question: '',
  
  // Conversation memory
  chat_history: [],      // Array of {role, content}
  summary: '',           // Summary of previous conversation
  
  // Query processing
  rewritten_query: '',
  sub_queries: [],       // For multi-part questions
  
  // Retrieval results
  retrieved_docs: [],    // Documents from search
  context: '',           // Combined context from docs
  
  // Agent reasoning
  reasoning_steps: [],   // Steps taken by the agent
  current_query: '',     // Current sub-query being processed
  agent_responses: [],   // Responses from parallel agents
  
  // Final output
  answer: '',
  sources: [],           // Source documents used
  
  // Control flow
  needs_clarification: false,
  clarification_question: '',
  is_multimodal: false,
  
  // Metadata
  user_id: '',
  session_id: '',
  timestamp: ''
};

/**
 * Create initial state for a new query
 */
export function createInitialState(question, userId = '', sessionId = '') {
  return {
    ...INITIAL_STATE,
    question,
    user_id: userId,
    session_id: sessionId,
    timestamp: new Date().toISOString()
  };
}

/**
 * Update state with chat history
 */
export function addToHistory(state, role, content) {
  return {
    ...state,
    chat_history: [
      ...state.chat_history,
      { role, content, timestamp: new Date().toISOString() }
    ]
  };
}

/**
 * Update state with retrieval results
 */
export function addRetrievalResults(state, docs, sourceDocs = []) {
  return {
    ...state,
    retrieved_docs: docs,
    sources: sourceDocs || docs.map(d => ({
      title: d.metadata?.source || 'Unknown',
      url: d.metadata?.url || ''
    }))
  };
}

/**
 * Update state with final answer
 */
export function setFinalAnswer(state, answer) {
  return {
    ...state,
    answer,
    chat_history: addToHistory(state, 'assistant', answer).chat_history,
    summary: state.question  // Simple summary for now
  };
}

/**
 * Check if clarification is needed
 */
export function needsClarification(state) {
  return {
    ...state,
    needs_clarification: true,
    clarification_question: state.clarification_question
  };
}

export default {
  INITIAL_STATE,
  createInitialState,
  addToHistory,
  addRetrievalResults,
  setFinalAnswer,
  needsClarification
};