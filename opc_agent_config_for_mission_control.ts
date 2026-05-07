// OPC项目专用的Mission Control智能体配置
// 需要复制到: /home/goose/.openclaw/mission-control-app/lib/config.ts

// Agent configuration - users customize this
export const AGENT_CONFIG = {
  // Branding
  brand: {
    name: 'OPC Mission Control',
    subtitle: '加密货币智能体指挥中心',
  },

  // Define your agent team here
  agents: [
    // 团队领导
    { id: 'lead', name: '指挥中心', emoji: '🎯', role: '团队领导', focus: '任务分配、策略规划、进度监控' },
    // 加密货币监控智能体
    { id: 'crypto-monitor', name: '加密货币监控', emoji: '📈', role: '市场监控', focus: '价格监控、趋势分析、交易信号' },
    // 智能合约开发智能体
    { id: 'smart-contract', name: '智能合约', emoji: '📝', role: '合约开发', focus: 'Solidity开发、安全审查、测试部署' },
    // 求职助手智能体
    { id: 'job-assistant', name: '求职助手', emoji: '💼', role: '职业发展', focus: '职位搜索、简历优化、面试准备' },
    // 交易辅助智能体
    { id: 'trading-helper', name: '交易辅助', emoji: '💰', role: '交易支持', focus: '策略回测、风险管理、组合优化' },
    // 前端开发智能体
    { id: 'frontend-dev', name: '前端开发', emoji: '🎨', role: '界面设计', focus: '仪表板设计、用户体验、响应式布局' },
    // 数据分析智能体
    { id: 'data-analyst', name: '数据分析', emoji: '📊', role: '数据分析', focus: '数据清洗、统计分析、可视化' },
    // 文档管理智能体
    { id: 'document-manager', name: '文档管理', emoji: '📚', role: '文档维护', focus: '文档编写、知识管理、报告生成' },
  ] as const,
};

// Derive AgentId type from config
export type AgentId = typeof AGENT_CONFIG.agents[number]['id'];

// Helper to get agent by ID
export function getAgentById(id: string) {
  return AGENT_CONFIG.agents.find(a => a.id === id);
}

// 任务类别配置
export const TASK_CATEGORIES = [
  { id: 'crypto', name: '加密货币', color: 'bg-green-100 text-green-800' },
  { id: 'contract', name: '智能合约', color: 'bg-blue-100 text-blue-800' },
  { id: 'job', name: '求职助手', color: 'bg-purple-100 text-purple-800' },
  { id: 'trading', name: '交易辅助', color: 'bg-yellow-100 text-yellow-800' },
  { id: 'frontend', name: '前端开发', color: 'bg-pink-100 text-pink-800' },
  { id: 'data', name: '数据分析', color: 'bg-indigo-100 text-indigo-800' },
  { id: 'document', name: '文档管理', color: 'bg-gray-100 text-gray-800' },
  { id: 'general', name: '通用任务', color: 'bg-gray-100 text-gray-800' },
] as const;

// 任务状态配置
export const TASK_STATUSES = [
  { id: 'backlog', name: '待办', color: 'bg-gray-100' },
  { id: 'todo', name: '待处理', color: 'bg-blue-100' },
  { id: 'in-progress', name: '进行中', color: 'bg-yellow-100' },
  { id: 'review', name: '审核中', color: 'bg-purple-100' },
  { id: 'done', name: '已完成', color: 'bg-green-100' },
] as const;

// 优先级配置
export const PRIORITY_LEVELS = [
  { id: 'low', name: '低', color: 'bg-gray-100' },
  { id: 'medium', name: '中', color: 'bg-blue-100' },
  { id: 'high', name: '高', color: 'bg-yellow-100' },
  { id: 'urgent', name: '紧急', color: 'bg-red-100' },
] as const;