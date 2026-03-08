#!/usr/bin/env node
/**
 * Financial RAG - CLI Chat Interface
 */

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import readline from 'readline';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const CONFIG = {
  SYSTEM_PROMPT: `你是专业的金融领域问答助手。

基于提供的金融研究报告信息，回答用户的问题。

## 回答原则：
1. 准确性：只基于检索到的信息回答
2. 专业性：使用金融专业术语
3. 完整性：覆盖问题的多个方面
4. 溯源性：注明信息来源

## 回复格式：
1. 直接回答问题
2. 如有数据，提供具体数值和日期
3. 列出主要参考来源
4. 如信息不足，坦诚说明`,

  WELCOME: `
============================================================
📈 Financial RAG System - CLI Chat
============================================================

输入问题进行金融领域问答。
输入 'quit' 退出，'clear' 清空对话历史，'stats' 查看状态。

============================================================
`
};

async function main() {
  console.log(CONFIG.WELCOME);
  
  // Simple in-memory "retrieval" (since we don't have full setup)
  // In production, this would use the actual RAG system
  
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
  
  const chatHistory = [];
  
  const askQuestion = async (question) => {
    // Add to history
    chatHistory.push({ role: 'user', content: question });
    
    console.log('\n⏳ 思考中...\n');
    
    // Simulate RAG response (placeholder for real implementation)
    const response = await simulateRAG(question, chatHistory);
    
    // Add assistant response
    chatHistory.push({ role: 'assistant', content: response.answer });
    
    console.log(response.answer);
    console.log('\n' + '='.repeat(50));
  };
  
  // Simulate RAG (placeholder)
  async function simulateRAG(query, history) {
    // In real implementation:
    // 1. Rewrite query based on history
    // 2. Search vector DB
    // 3. Generate answer with context
    
    await new Promise(r => setTimeout(r, 500)); // Simulate processing
    
    // Simple keyword-based response for demo
    const responses = {
      'ai': `根据最新行业报告，**人工智能行业在2026年呈快速发展态势**：

## 关键趋势：
1. **市场规模增长**：AI行业持续高速扩张
2. **应用场景拓展**：从技术层面向产业落地延伸
3. **投资活跃度提升**：资本市场持续关注

## 风险提示：
- 技术迭代速度快
- 竞争格局激烈
- 监管政策变化

*注：此为示例回复，实际使用需完整初始化RAG系统*`,
      
      '新能源': `根据行业研究报告，**新能源汽车行业2026年展望**：

## 主要特点：
1. **渗透率提升**：新能源汽车市场份额继续扩大
2. **技术创新**：电池技术、智能驾驶持续突破
3. **产业链整合**：上下游协同发展

## 推荐关注：
- 锂电池龙头企业
- 智能驾驶解决方案
- 充电基础设施

*注：此为示例回复，实际使用需完整初始化RAG系统*`,
      
      'default': `📊 关于"${query}"，我需要更多信息来回答。

以下是可以尝试的问题方向：
- 人工智能行业趋势
- 新能源汽车行业分析
- 半导体行业前景
- 宏观经济展望

💡 **提示**：请先运行完整初始化：

\`\`\`bash
cd ~/.openclaw/workspace/finance_rag
npm install
node scripts/setup_db.mjs
node scripts/app.mjs
\`\`\`

然后使用 Web 界面进行更准确的问答！`
    };
    
    const queryLower = query.toLowerCase();
    let answer = responses.default;
    
    if (queryLower.includes('ai') || queryLower.includes('人工智能')) {
      answer = responses.ai;
    } else if (queryLower.includes('新能源') || queryLower.includes('电动车')) {
      answer = responses.responses['新能源'];
    }
    
    return {
      answer,
      sources: ['模拟检索'],
      confidence: 0.8
    };
  }
  
  // Chat loop
  const chat = () => {
    rl.question('你: ', async (input) => {
      const question = input.trim();
      
      if (!question) {
        chat();
        return;
      }
      
      if (question.toLowerCase() === 'quit' || question.toLowerCase() === 'exit') {
        console.log('\n👋 再见！感谢使用 Financial RAG System');
        rl.close();
        return;
      }
      
      if (question.toLowerCase() === 'clear') {
        chatHistory.length = 0;
        console.log('\n✅ 对话历史已清空\n');
        chat();
        return;
      }
      
      if (question.toLowerCase() === 'stats') {
        console.log(`
📊 系统状态：
- 对话轮数：${Math.floor(chatHistory.length / 2)}
- 系统版本：v1.0.0
- 状态：CLI模式（需初始化完整RAG使用Web UI）
        `);
        chat();
        return;
      }
      
      await askQuestion(question);
      chat();
    });
  };
  
  chat();
}

main().catch(console.error);