/**
 * 配置模板的 schema（原型 02-配置模板-*.png 共 7 张 + 11-配置模板-工具模板.png）。
 *
 * 这 8 张画布是同一个页面的不同数据：返回箭头 + 简介卡 + 模板配置卡 + 取消/创建。
 * 所以前端只写一个 TemplateConfigView，靠这张表驱动字段。
 */

export type FieldControl = 'text' | 'textarea' | 'select' | 'switch' | 'slider' | 'tags' | 'upload'

export interface TemplateField {
  key: string
  label: string
  control: FieldControl
  placeholder?: string
  options?: string[]
  required?: boolean
  hint?: string
  rows?: number
  max?: number
  /** 占满两列（长文本或上传区） */
  block?: boolean
  defaultValue?: string | number | boolean | string[]
}

export interface TemplateSection {
  title: string
  description?: string
  fields: TemplateField[]
}

export interface TemplateSchema {
  key: string
  /** 页面标题，如「配置模板: 聊天机器人」 */
  title: string
  /** 简介卡文案 */
  description: string
  icon: string
  /** 提交后创建到哪个实体 */
  creates: 'agent' | 'prompt' | 'workflow' | 'dataset' | 'app' | 'tool'
  sections: TemplateSection[]
}

export const TEMPLATE_SCHEMAS: Record<string, TemplateSchema> = {
  chatbot: {
    key: 'chatbot',
    title: '配置模板: 聊天机器人',
    description: '基于知识库的客服聊天机器人，会按你选择的模型与知识库创建一条 Agent 记录。',
    icon: 'mdi-message-text-outline',
    creates: 'agent',
    sections: [
      {
        title: '模板配置',
        fields: [
          { key: 'name', label: 'Agent 名称', control: 'text', required: true, defaultValue: '聊天机器人' },
          { key: 'description', label: '描述', control: 'text', defaultValue: '基于知识库的智能客服聊天机器人' },
          { key: 'model', label: '模型', control: 'select', options: ['gpt-4o', 'gpt-4o-mini', 'claude-3-5-sonnet', 'deepseek-chat'], defaultValue: 'gpt-4o' },
          { key: 'knowledge', label: '关联知识库', control: 'select', options: ['产品文档知识库', 'FAQ知识库', '技术文档库'], defaultValue: '产品文档知识库' },
          { key: 'greeting', label: '欢迎语', control: 'textarea', rows: 2, block: true, defaultValue: '你好，我是智能客服助手，请问有什么可以帮你？' },
          { key: 'temperature', label: '温度', control: 'slider', hint: '推荐 0.7，越低越稳定' }
        ]
      }
    ]
  },
  'code-assistant': {
    key: 'code-assistant',
    title: '配置模板: 代码助手',
    description: '面向代码审查与补全的 Agent 模板，默认使用更严格的提示词。',
    icon: 'mdi-code-tags',
    creates: 'agent',
    sections: [
      {
        title: '模板配置',
        fields: [
          { key: 'name', label: 'Agent 名称', control: 'text', required: true, defaultValue: '代码助手' },
          { key: 'language', label: '主要语言', control: 'select', options: ['TypeScript', 'Python', 'Java', 'Go'], defaultValue: 'TypeScript' },
          { key: 'rules', label: '审查规则', control: 'textarea', rows: 3, block: true, defaultValue: '从可读性、安全性、性能三方面审查；指出问题时给出修改后的代码。' }
        ]
      }
    ]
  },
  workflow: {
    key: 'workflow',
    title: '配置模板: 工作流模板',
    description: '从模板创建一个带初始节点的工作流，创建后可以直接进画布继续编辑。',
    icon: 'mdi-sitemap-outline',
    creates: 'workflow',
    sections: [
      {
        title: '模板配置',
        fields: [
          { key: 'name', label: '工作流名称', control: 'text', required: true, defaultValue: '文档处理流' },
          { key: 'description', label: '描述', control: 'text', defaultValue: '上传文档 → 解析 → 摘要 → 归档' },
          { key: 'trigger', label: '触发方式', control: 'select', options: ['手动触发', '定时触发', 'Webhook', '应用调用'], defaultValue: '手动触发' },
          { key: 'timeout', label: '超时时间（秒）', control: 'text', defaultValue: '300' },
          { key: 'note', label: '备注', control: 'textarea', rows: 3, block: true }
        ]
      }
    ]
  },
  app: {
    key: 'app',
    title: '配置模板: 应用模板',
    description: '把 Agent 或工作流包装成对外可用的应用，创建后状态为草稿。',
    icon: 'mdi-view-grid-outline',
    creates: 'app',
    sections: [
      {
        title: '模板配置',
        fields: [
          { key: 'name', label: '应用名称', control: 'text', required: true, defaultValue: '智能客服应用' },
          { key: 'description', label: '描述', control: 'text', defaultValue: '面向官网访客的客服入口' },
          { key: 'type', label: '应用类型', control: 'select', options: ['聊天机器人', '智能体', '工作流应用'], defaultValue: '聊天机器人' },
          { key: 'access', label: '访问方式', control: 'select', options: ['公开', '登录后可用', '仅内网'], defaultValue: '公开' },
          { key: 'welcome', label: '首屏提示', control: 'textarea', rows: 2, block: true, defaultValue: '有什么可以帮你的？' }
        ]
      }
    ]
  },
  agent: {
    key: 'agent',
    title: '配置模板: 智能体模板',
    description: '带推理策略与工具绑定的 Agent 模板，适合多步任务。',
    icon: 'mdi-robot-outline',
    creates: 'agent',
    sections: [
      {
        title: '模板配置',
        fields: [
          { key: 'name', label: 'Agent 名称', control: 'text', required: true, defaultValue: '智能体助手' },
          { key: 'strategy', label: '推理策略', control: 'select', options: ['Function Calling', 'ReAct', 'Chain of Thought'], defaultValue: 'Function Calling' },
          { key: 'tools', label: '绑定工具', control: 'tags', hint: '输入工具名后回车，最多 5 个' },
          { key: 'prompt', label: '系统提示词', control: 'textarea', rows: 4, block: true, defaultValue: '你是一个可以调用工具的智能体，请先规划再执行。' }
        ]
      }
    ]
  },
  prompt: {
    key: 'prompt',
    title: '配置模板: 提示词模板',
    description: '预置变量的提示词模板，创建后可在编辑器里继续调。',
    icon: 'mdi-code-braces',
    creates: 'prompt',
    sections: [
      {
        title: '模板配置',
        fields: [
          { key: 'name', label: '提示词名称', control: 'text', required: true, defaultValue: '客服话术优化' },
          { key: 'category', label: '分类', control: 'select', options: ['通用', '客服', '开发', '内容创作', '办公', '数据分析'], defaultValue: '通用' },
          { key: 'template', label: '提示词内容', control: 'textarea', rows: 6, block: true, defaultValue: '你是客服专家。请把下面的答复改写得更共情、更具体：\n{{input}}' },
          { key: 'variables', label: '变量', control: 'tags', hint: '模板里用 {{变量名}} 引用' }
        ]
      }
    ]
  },
  dataset: {
    key: 'dataset',
    title: '配置模板: 数据集模板',
    description: '创建一条待解析的数据集，与知识库不同：这里产出结构化记录。',
    icon: 'mdi-database-outline',
    creates: 'dataset',
    sections: [
      {
        title: '模板配置',
        fields: [
          { key: 'name', label: '数据集名称', control: 'text', required: true, defaultValue: '产品知识库' },
          { key: 'description', label: '描述', control: 'text', defaultValue: '产品手册结构化后的问答数据' },
          { key: 'type', label: '数据类型', control: 'select', options: ['文档', '问答对', '表格'], defaultValue: '文档' },
          { key: 'encoding', label: '文件编码', control: 'select', options: ['UTF-8', 'GBK'], defaultValue: 'UTF-8' },
          { key: 'files', label: '数据文件', control: 'upload', block: true, hint: '支持 CSV / JSONL / PDF，单个不超过 50 MB' }
        ]
      }
    ]
  },
  tool: {
    key: 'tool',
    title: '配置模板: 工具模板',
    description: '把内部 API 包装成 Agent 可调用的工具，创建后可在工具列表里测试。',
    icon: 'mdi-wrench-outline',
    creates: 'tool',
    sections: [
      {
        title: '模板配置',
        fields: [
          { key: 'name', label: '工具名称', control: 'text', required: true, defaultValue: '订单查询' },
          { key: 'description', label: '描述', control: 'text', defaultValue: '根据订单号查询物流状态' },
          { key: 'type', label: '工具类型', control: 'select', options: ['内置', '自定义API'], defaultValue: '内置' },
          { key: 'params', label: '输入参数', control: 'text', block: true, defaultValue: 'orderId, withDetail' },
          { key: 'schema', label: '参数 Schema', control: 'textarea', rows: 3, block: true, defaultValue: '{"orderId":"string","withDetail":"boolean"}' }
        ]
      }
    ]
  }
}

/** 侧栏/路由用到的 key 顺序（与原型画板顺序一致） */
export const TEMPLATE_KEYS = [
  'chatbot',
  'code-assistant',
  'workflow',
  'app',
  'agent',
  'prompt',
  'dataset',
  'tool'
]
