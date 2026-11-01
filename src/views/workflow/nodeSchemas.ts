/**
 * 工作流节点类型与配置 schema。
 *
 * 原型 03-工作流-节点库-*.png 一共 9 张画布，每张对应一种节点被选中时的右侧属性面板。
 * 这里把 10 种节点（开始 / LLM / Agent / 知识检索 / 问答 / 代码执行 / HTTP请求 / 数据转换 /
 * 条件判断 / 结束）的字段收敛成一张表，属性面板按节点类型渲染。
 *
 * 原型里 Agent 与「问答」两个节点的配置区是空的 —— 那是原型缺失，不是「该节点无配置」，
 * 这里按需补齐。
 */

export type NodeFieldControl = 'text' | 'textarea' | 'select' | 'slider' | 'number' | 'tags' | 'code'

export interface NodeField {
  key: string
  label: string
  control: NodeFieldControl
  placeholder?: string
  hint?: string
  options?: string[]
  rows?: number
  min?: number
  max?: number
  step?: number
  defaultValue?: string | number | string[]
}

export interface NodeTypeMeta {
  type: string
  label: string
  icon: string
  /** 节点色系：起止节点 vs 处理节点 vs 分支节点 */
  tone: 'terminal' | 'process' | 'branch'
  description: string
  fields: NodeField[]
}

export const NODE_TYPES: NodeTypeMeta[] = [
  {
    type: 'start',
    label: '开始',
    icon: 'mdi-play-circle-outline',
    tone: 'terminal',
    description: '工作流入口，定义输入变量',
    fields: [
      { key: 'inputs', label: '输入变量', control: 'tags', hint: '回车添加，如 query、userId', defaultValue: ['query'] },
      { key: 'note', label: '说明', control: 'textarea', rows: 2, placeholder: '这个工作流接收什么' }
    ]
  },
  {
    type: 'llm',
    label: 'LLM',
    icon: 'mdi-brain',
    tone: 'process',
    description: '调用大模型生成内容',
    fields: [
      {
        key: 'model',
        label: '模型',
        control: 'select',
        options: ['gpt-4o', 'gpt-4o-mini', 'claude-3-5-sonnet', 'deepseek-chat'],
        defaultValue: 'gpt-4o'
      },
      { key: 'system', label: '系统提示词', control: 'textarea', rows: 4, placeholder: '你是一个……' },
      { key: 'temperature', label: '温度', control: 'slider', min: 0, max: 1, step: 0.1, defaultValue: 0.7 },
      { key: 'output', label: '输出变量', control: 'text', defaultValue: 'llm_output' }
    ]
  },
  {
    type: 'agent',
    label: 'Agent',
    icon: 'mdi-robot-outline',
    tone: 'process',
    description: '调用一个已创建的 Agent',
    fields: [
      {
        key: 'agent',
        label: 'Agent',
        control: 'select',
        options: ['智能客服助手', '内容创作助手', '销售支持专家', '数据分析师'],
        defaultValue: '智能客服助手'
      },
      { key: 'maxTurns', label: '最大轮数', control: 'number', defaultValue: 5 },
      { key: 'output', label: '输出变量', control: 'text', defaultValue: 'agent_output' }
    ]
  },
  {
    type: 'retrieval',
    label: '知识检索',
    icon: 'mdi-book-search-outline',
    tone: 'process',
    description: '从知识库召回相关分块',
    fields: [
      {
        key: 'knowledge',
        label: '知识库',
        control: 'select',
        options: ['产品文档知识库', 'FAQ知识库', '技术文档库'],
        defaultValue: '产品文档知识库'
      },
      { key: 'topK', label: '召回条数', control: 'number', defaultValue: 5 },
      { key: 'threshold', label: '相似度阈值', control: 'slider', min: 0, max: 1, step: 0.05, defaultValue: 0.75 },
      { key: 'output', label: '输出变量', control: 'text', defaultValue: 'chunks' }
    ]
  },
  {
    type: 'qa',
    label: '问答',
    icon: 'mdi-comment-question-outline',
    tone: 'process',
    description: '按问题模板从上下文抽答案',
    fields: [
      { key: 'question', label: '问题模板', control: 'textarea', rows: 3, defaultValue: '{{query}}' },
      { key: 'context', label: '上下文变量', control: 'text', defaultValue: 'chunks' },
      { key: 'output', label: '输出变量', control: 'text', defaultValue: 'answer' }
    ]
  },
  {
    type: 'code',
    label: '代码执行',
    icon: 'mdi-code-braces',
    tone: 'process',
    description: '在沙箱里跑一段代码',
    fields: [
      { key: 'language', label: '语言', control: 'select', options: ['Python', 'JavaScript'], defaultValue: 'Python' },
      { key: 'code', label: '代码', control: 'code', rows: 6, defaultValue: 'def main(inputs):\n    return {"ok": True}' },
      { key: 'timeout', label: '超时（秒）', control: 'number', defaultValue: 30 }
    ]
  },
  {
    type: 'http',
    label: 'HTTP请求',
    icon: 'mdi-web',
    tone: 'process',
    description: '调用外部 API',
    fields: [
      { key: 'method', label: '方法', control: 'select', options: ['GET', 'POST', 'PUT', 'DELETE'], defaultValue: 'GET' },
      { key: 'url', label: 'URL', control: 'text', placeholder: 'https://api.example.com/v1/query' },
      { key: 'headers', label: '请求头', control: 'textarea', rows: 3, defaultValue: '{\n  "Content-Type": "application/json"\n}' },
      { key: 'timeout', label: '超时（秒）', control: 'number', defaultValue: 10 }
    ]
  },
  {
    type: 'transform',
    label: '数据转换',
    icon: 'mdi-swap-horizontal',
    tone: 'process',
    description: '在节点之间转换数据结构',
    fields: [
      {
        key: 'mode',
        label: '转换类型',
        control: 'select',
        options: ['字段映射', 'JSON 解析', '数组展平', '模板渲染'],
        defaultValue: '字段映射'
      },
      { key: 'rule', label: '规则', control: 'textarea', rows: 3, placeholder: '{"source":"chunks","target":"context"}' },
      { key: 'onError', label: '错误处理', control: 'select', options: ['中断', '跳过', '使用默认值'], defaultValue: '中断' }
    ]
  },
  {
    type: 'condition',
    label: '条件判断',
    icon: 'mdi-source-branch',
    tone: 'branch',
    description: '按表达式分流',
    fields: [
      { key: 'expression', label: '表达式', control: 'text', defaultValue: 'len(chunks) > 0' },
      { key: 'branches', label: '分支标签', control: 'tags', defaultValue: ['命中', '未命中'] }
    ]
  },
  {
    type: 'end',
    label: '结束',
    icon: 'mdi-stop-circle-outline',
    tone: 'terminal',
    description: '工作流出口，定义输出',
    fields: [{ key: 'output', label: '输出变量', control: 'text', defaultValue: 'answer' }]
  }
]

export const NODE_META_MAP: Record<string, NodeTypeMeta> = Object.fromEntries(
  NODE_TYPES.map((item) => [item.type, item])
)

export interface CanvasNode {
  id: string
  type: string
  x: number
  y: number
  /** 用户改过的节点名 */
  label?: string
  /** 各节点类型的配置值 */
  config: Record<string, unknown>
}

export interface CanvasEdge {
  id: string
  from: string
  to: string
  /** 分支节点的标签（命中/未命中） */
  label?: string
}

/** 新建节点时按 schema 生成默认配置 */
export function defaultConfigFor(type: string): Record<string, unknown> {
  const meta = NODE_META_MAP[type]
  if (!meta) return {}
  const config: Record<string, unknown> = {}
  for (const field of meta.fields) {
    if (field.defaultValue !== undefined) config[field.key] = field.defaultValue
    else if (field.control === 'tags') config[field.key] = []
    else if (field.control === 'slider' || field.control === 'number') config[field.key] = field.min ?? 0
    else config[field.key] = ''
  }
  return config
}

export const NODE_WIDTH = 168
export const NODE_HEIGHT = 56
