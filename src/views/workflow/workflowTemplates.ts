/**
 * 创建工作流页的模板库（原型 03-工作流-创建.png）。
 * 9 个分类 + 10 个模板；「空白工作流」不弹窗，直接进画布。
 */

export interface WorkflowTemplate {
  key: string
  name: string
  /** 聊天流 / 工作流 */
  type: '聊天流' | '工作流'
  /** 简单 / 中等 / 复杂 */
  difficulty: '简单' | '中等' | '复杂'
  description: string
  /** 预计搭建时间 */
  minutes: number
  /** 功能标签 chips */
  tags: string[]
  /** 归属分类 */
  category: string
  icon: string
  /** 弹窗里预填时的初始节点数 */
  nodeCount: number
}

export const WORKFLOW_CATEGORIES = [
  '全部',
  '客服',
  '文档处理',
  '语音处理',
  '开发工具',
  '办公自动化',
  '数据分析',
  'AI代理',
  '自定义'
] as const

export const WORKFLOW_TEMPLATES: WorkflowTemplate[] = [
  {
    key: 'chatbot',
    name: '智能聊天机器人',
    type: '聊天流',
    difficulty: '简单',
    description: '基于知识库的智能客服聊天机器人，支持多轮对话和上下文理解',
    minutes: 10,
    tags: ['知识库检索', '多轮对话', '情绪分析'],
    category: '客服',
    icon: 'mdi-message-text-outline',
    nodeCount: 5
  },
  {
    key: 'doc-qa',
    name: '文档问答系统',
    type: '工作流',
    difficulty: '中等',
    description: '上传文档并基于文档内容进行智能问答',
    minutes: 15,
    tags: ['文档解析', 'RAG检索', '答案生成'],
    category: '文档处理',
    icon: 'mdi-file-document-outline',
    nodeCount: 7
  },
  {
    key: 'translator',
    name: '多语言翻译器',
    type: '工作流',
    difficulty: '简单',
    description: '支持多种语言互译的智能翻译工作流',
    minutes: 8,
    tags: ['语言检测', '翻译', '质量评估'],
    category: '办公自动化',
    icon: 'mdi-translate',
    nodeCount: 4
  },
  {
    key: 'code-review',
    name: '代码审查助手',
    type: '工作流',
    difficulty: '复杂',
    description: '自动化代码审查，检查代码质量、安全性和最佳实践',
    minutes: 25,
    tags: ['代码分析', '安全检测', '建议生成'],
    category: '开发工具',
    icon: 'mdi-code-tags',
    nodeCount: 9
  },
  {
    key: 'mail-sort',
    name: '邮件智能分类',
    type: '工作流',
    difficulty: '中等',
    description: '自动分类和分发邮件，提取关键信息并分配优先级',
    minutes: 20,
    tags: ['邮件解析', '分类', '优先级排序'],
    category: '办公自动化',
    icon: 'mdi-email-outline',
    nodeCount: 6
  },
  {
    key: 'data-report',
    name: '数据分析报告',
    type: '工作流',
    difficulty: '复杂',
    description: '自动分析数据并生成可视化报告',
    minutes: 30,
    tags: ['数据处理', '统计分析', '报告生成'],
    category: '数据分析',
    icon: 'mdi-chart-box-outline',
    nodeCount: 11
  },
  {
    key: 'ai-agent',
    name: 'AI智能代理',
    type: '工作流',
    difficulty: '复杂',
    description: '具备推理能力的AI代理，可以执行复杂任务',
    minutes: 35,
    tags: ['任务规划', '工具调用', '多步推理'],
    category: 'AI代理',
    icon: 'mdi-robot-outline',
    nodeCount: 12
  },
  {
    key: 'content-review',
    name: '内容审核流程',
    type: '工作流',
    difficulty: '中等',
    description: '敏感词 + 语义双重审核，命中后转人工复核',
    minutes: 18,
    tags: ['敏感词', '语义审核', '人工复核'],
    category: '文档处理',
    icon: 'mdi-shield-check-outline',
    nodeCount: 6
  },
  {
    key: 'speech',
    name: '语音转写助手',
    type: '工作流',
    difficulty: '中等',
    description: '长音频转写并按段落结构化摘要',
    minutes: 22,
    tags: ['语音识别', '分段', '摘要'],
    category: '语音处理',
    icon: 'mdi-microphone-outline',
    nodeCount: 5
  },
  {
    key: 'blank',
    name: '空白工作流',
    type: '工作流',
    difficulty: '简单',
    description: '从头开始创建自定义工作流',
    minutes: 0,
    tags: [],
    category: '自定义',
    icon: 'mdi-plus-box-outline',
    nodeCount: 1
  }
]
