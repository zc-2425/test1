/**
 * 探索页的模板目录（原型 02-探索.png：总模板数 16）。
 *
 * 一共 16 项，正好对上原型的「16 总模板数」：
 * 8 个「配置模板」+ 8 个「工作流模板」。
 * 每项都指向真实可用的落地页：
 *   target.kind = 'config'   → /explore/template/:key/config
 *   target.kind = 'workflow' → /workflow/create?template=:key&modal=1
 */

export interface TemplateCard {
  key: string
  name: string
  description: string
  icon: string
  /** 探索页的分类 chips */
  category: string
  rating: number
  usageCount: number
  /** HOT 角标 */
  hot: boolean
  /** 上架日期，用于「最新」排序 */
  addedAt: string
  target: { kind: 'config' | 'workflow'; key: string }
}

export const EXPLORE_CATEGORIES = [
  '全部',
  'AI助手',
  '内容创作',
  '开发工具',
  '创意设计',
  '数据分析',
  '办公工具',
  '营销推广',
  '教育学习',
  '专业服务'
] as const

export const EXPLORE_TEMPLATES: TemplateCard[] = [
  // ——— 8 个配置模板 ———
  {
    key: 'cfg-chatbot',
    name: '聊天机器人',
    description: '创建一个能基于知识库回答问题的对话机器人，支持多轮对话和上下文理解。',
    icon: 'mdi-message-text-outline',
    category: 'AI助手',
    rating: 4.8,
    usageCount: 1250,
    hot: true,
    addedAt: '2024-01-15',
    target: { kind: 'config', key: 'chatbot' }
  },
  {
    key: 'cfg-code-assistant',
    name: '代码助手',
    description: '协助编写、调试和优化代码，支持多种编程语言。',
    icon: 'mdi-code-tags',
    category: '开发工具',
    rating: 4.9,
    usageCount: 1100,
    hot: true,
    addedAt: '2024-01-14',
    target: { kind: 'config', key: 'code-assistant' }
  },
  {
    key: 'cfg-workflow',
    name: '工作流模板',
    description: '从预置模板快速生成一条带初始节点的工作流，创建后可直接进画布编辑。',
    icon: 'mdi-sitemap-outline',
    category: '办公工具',
    rating: 4.6,
    usageCount: 860,
    hot: false,
    addedAt: '2024-01-13',
    target: { kind: 'config', key: 'workflow' }
  },
  {
    key: 'cfg-app',
    name: '应用模板',
    description: '把 Agent 或工作流包装成对外可用的应用，带访问方式与首屏提示配置。',
    icon: 'mdi-view-grid-outline',
    category: '专业服务',
    rating: 4.5,
    usageCount: 640,
    hot: false,
    addedAt: '2024-01-12',
    target: { kind: 'config', key: 'app' }
  },
  {
    key: 'cfg-agent',
    name: '智能体模板',
    description: '带推理策略与工具绑定的智能体，适合多步任务与工具调用场景。',
    icon: 'mdi-robot-outline',
    category: 'AI助手',
    rating: 4.7,
    usageCount: 980,
    hot: true,
    addedAt: '2024-01-11',
    target: { kind: 'config', key: 'agent' }
  },
  {
    key: 'cfg-prompt',
    name: '提示词模板',
    description: '预置变量的提示词模板，创建后可在编辑器里继续调与测试。',
    icon: 'mdi-code-braces',
    category: '内容创作',
    rating: 4.7,
    usageCount: 1350,
    hot: true,
    addedAt: '2024-01-10',
    target: { kind: 'config', key: 'prompt' }
  },
  {
    key: 'cfg-dataset',
    name: '数据集模板',
    description: '创建一条待解析的数据集，产出结构化记录，与知识库的向量化链路不同。',
    icon: 'mdi-database-outline',
    category: '数据分析',
    rating: 4.4,
    usageCount: 520,
    hot: false,
    addedAt: '2024-01-09',
    target: { kind: 'config', key: 'dataset' }
  },
  {
    key: 'cfg-tool',
    name: '工具模板',
    description: '把内部 API 包装成 Agent 可调用的工具，含参数说明与 JSON Schema。',
    icon: 'mdi-wrench-outline',
    category: '开发工具',
    rating: 4.5,
    usageCount: 760,
    hot: false,
    addedAt: '2024-01-08',
    target: { kind: 'config', key: 'tool' }
  },

  // ——— 8 个工作流模板 ———
  {
    key: 'wf-chatbot',
    name: '智能聊天机器人流',
    description: '知识库检索 + 多轮对话 + 情绪分析的完整工作流，适合客服场景。',
    icon: 'mdi-forum-outline',
    category: 'AI助手',
    rating: 4.8,
    usageCount: 1420,
    hot: true,
    addedAt: '2024-01-15',
    target: { kind: 'workflow', key: 'chatbot' }
  },
  {
    key: 'wf-doc-qa',
    name: '文档问答系统',
    description: '上传文档后自动解析并基于内容智能问答，带引用来源。',
    icon: 'mdi-file-document-outline',
    category: '办公工具',
    rating: 4.7,
    usageCount: 1180,
    hot: false,
    addedAt: '2024-01-14',
    target: { kind: 'workflow', key: 'doc-qa' }
  },
  {
    key: 'wf-translator',
    name: '语言翻译器',
    description: '在不同语言之间进行准确翻译，支持术语表与质量评估。',
    icon: 'mdi-translate',
    category: '教育学习',
    rating: 4.7,
    usageCount: 1350,
    hot: false,
    addedAt: '2024-01-13',
    target: { kind: 'workflow', key: 'translator' }
  },
  {
    key: 'wf-code-review',
    name: '代码审查流水线',
    description: '静态检查 + LLM 语义审查双通道，输出可执行的修改建议。',
    icon: 'mdi-source-branch',
    category: '开发工具',
    rating: 4.6,
    usageCount: 890,
    hot: false,
    addedAt: '2024-01-12',
    target: { kind: 'workflow', key: 'code-review' }
  },
  {
    key: 'wf-mail-sort',
    name: '邮件智能分类',
    description: '自动分类收件箱、提取关键信息并分配优先级。',
    icon: 'mdi-email-outline',
    category: '办公工具',
    rating: 4.4,
    usageCount: 620,
    hot: false,
    addedAt: '2024-01-11',
    target: { kind: 'workflow', key: 'mail-sort' }
  },
  {
    key: 'wf-data-report',
    name: '数据分析报告',
    description: '从数据集到可视化报告的自动链路，支持定时触发。',
    icon: 'mdi-chart-box-outline',
    category: '数据分析',
    rating: 4.8,
    usageCount: 980,
    hot: true,
    addedAt: '2024-01-10',
    target: { kind: 'workflow', key: 'data-report' }
  },
  {
    key: 'wf-ai-agent',
    name: 'AI 智能代理',
    description: '具备任务规划、工具调用与多步推理能力的代理工作流。',
    icon: 'mdi-robot-happy-outline',
    category: 'AI助手',
    rating: 4.9,
    usageCount: 760,
    hot: true,
    addedAt: '2024-01-09',
    target: { kind: 'workflow', key: 'ai-agent' }
  },
  {
    key: 'wf-content-review',
    name: '内容审核流程',
    description: '敏感词与语义双重审核，命中后自动转人工复核。',
    icon: 'mdi-shield-check-outline',
    category: '专业服务',
    rating: 4.5,
    usageCount: 540,
    hot: false,
    addedAt: '2024-01-08',
    target: { kind: 'workflow', key: 'content-review' }
  }
]

/** 生成「使用模板」要跳转的地址 */
export function templateTargetPath(template: TemplateCard): string {
  if (template.target.kind === 'config') {
    return `/explore/template/${template.target.key}/config`
  }
  return `/workflow/create?template=${template.target.key}&modal=1`
}
