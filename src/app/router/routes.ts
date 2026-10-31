import type { RouteRecordRaw } from 'vue-router'

/**
 * 全量路由表 —— 31 条（另有 2 个由 query 驱动的全局弹窗态：?alerts=1 / ?settings=1）。
 * 数据来源：docs/01-页面清单.md（62 画布去重后的结果）。
 *
 * 约定：
 * 1. meta.title 用截图上的大标题原文，不改写；
 * 2. meta.screen 指向 _ref/ 下的对照截图，P5–P10 实现时逐页对照；
 * 3. 现阶段所有页面都指向 StubView，逐页替换为真实组件即可，不需要动路由结构。
 */
const Stub = () => import('@/views/stubs/StubView.vue')

/** 全部业务页（挂在 AppShell 之下） */
export const shellRoutes: RouteRecordRaw[] = [
  // ===== 开发工具（不属于 62 画布的 31 条业务路由，仅本地调试用）=====
  {
    path: 'dev/ui',
    name: 'dev-ui',
    component: () => import('@/views/dev/ComponentPlayground.vue'),
    meta: {
      title: '组件预览',
      subtitle: 'P3 基础组件的视觉基线，数据走真实接口',
      module: '开发工具',
      phase: 'P3'
    }
  },
  // ================= 探索 =================
  {
    path: 'explore',
    name: 'explore',
    component: Stub,
    meta: {
      title: '探索 AI 模板',
      subtitle: '发现并使用各种 AI 模板，快速构建您的智能应用，从对话机器人到数据分析，应有尽有。',
      module: '探索',
      navKey: 'explore',
      skeleton: 'B',
      phase: 'P8',
      screen: '02-探索.png',
      todo: [
        '4 个统计卡（总模板数 16 / 热门模板 5 / 收藏模板 4 / 总使用次数 11.8K）',
        '搜索 + 10 个分类 chips + 排序下拉',
        '模板卡网格：HOT 角标 / 收藏心形 / 星级 / 使用量 / 使用模板按钮'
      ]
    }
  },
  {
    path: 'explore/template/:key/config',
    name: 'explore-template-config',
    component: Stub,
    meta: {
      title: '配置模板',
      module: '探索',
      navKey: 'explore',
      skeleton: 'E',
      phase: 'P7',
      screen: '02-配置模板-聊天机器人.png',
      todo: [
        '7 个模板共用一套 schema：聊天机器人/代码助手/工作流/应用/智能体/提示词/数据集',
        '返回箭头 + 简介卡 + 模板配置卡 + 取消/创建',
        '提示词模板的大文本域应升级为 CodeEditor'
      ]
    }
  },

  // ================= 工作流 =================
  {
    path: 'workflow/list',
    name: 'workflow-list',
    component: () => import('@/views/workflow/WorkflowListView.vue'),
    meta: {
      title: '工作流管理',
      module: '工作流',
      navKey: 'workflow',
      skeleton: 'A1',
      phase: 'P5',
      screen: '03-工作流管理.png',
      todo: [
        '主按钮「+ 创建新工作流」（原型为紫色胶囊）',
        '表格列按语义重建：工作流名｜类型｜状态｜节点数｜最后运行｜成功率｜创建时间｜操作',
        '行内 ▶ 运行 + ⋮ 更多；状态徽章 已发布/草稿/运行中'
      ]
    }
  },
  {
    path: 'workflow/create',
    name: 'workflow-create',
    component: Stub,
    meta: {
      title: '创建新工作流',
      subtitle: '选择模板快速开始，或创建空白工作流自定义构建',
      module: '工作流',
      navKey: 'workflow',
      skeleton: 'B',
      phase: 'P7',
      screen: '03-工作流-创建 .png',
      todo: [
        '9 个分类 chips：全部/客服/文档处理/语音处理/开发工具/办公自动化/数据分析/AI代理/自定义',
        '三列模板卡：图标/类型徽章+难度徽章/描述/预计时间/功能 chips/使用此模板',
        '「使用此模板」→ 打开创建工作流弹窗（?template=key&modal=1）'
      ]
    }
  },
  {
    path: 'workflow/:id/canvas',
    name: 'workflow-canvas',
    component: Stub,
    meta: {
      title: '工作流编辑器',
      module: '工作流',
      navKey: 'workflow',
      skeleton: 'D',
      phase: 'P9',
      screen: '03-工作流-节点库-LLM.png',
      hideSidebar: true,
      todo: [
        '三栏：节点库 10 项 / 点阵画布 / 节点属性面板',
        '节点类型 schema 驱动属性面板（开始/LLM/Agent/知识检索/问答/代码执行/HTTP请求/数据转换/条件判断/结束）',
        '补连线 + 自动布局（原型 9 张画布 0 条边且节点重叠）',
        '?node=<type> 选中态、?run=1 运行弹窗'
      ]
    }
  },

  // ================= 应用中心 =================
  {
    path: 'app/list',
    name: 'app-list',
    component: () => import('@/views/app/AppListView.vue'),
    meta: {
      title: '应用管理',
      module: '应用中心',
      navKey: 'app',
      skeleton: 'A1',
      phase: 'P5',
      screen: '04-应用管理.png',
      todo: ['右上「+ 创建应用」', '表格 7 列 ×10 行（卡片包裹）', '应用名点击 → 详情']
    }
  },
  {
    path: 'app/:id',
    name: 'app-detail',
    component: () => import('@/views/app/AppDetailView.vue'),
    meta: {
      title: '应用详情',
      module: '应用中心',
      navKey: 'app',
      skeleton: 'C',
      phase: 'P6',
      screen: '04-应用中心-智能客服助手.png',
      todo: ['左只读信息卡（2/3）+ 右快速操作卡（1/3）', '原型未画编辑态与详情分析页']
    }
  },

  // ================= 知识库 =================
  {
    path: 'knowledge/list',
    name: 'knowledge-list',
    component: () => import('@/views/knowledge/KnowledgeListView.vue'),
    meta: {
      title: '知识库管理',
      module: '知识库',
      navKey: 'knowledge',
      skeleton: 'A1',
      phase: 'P5',
      screen: '05-知识库管理.png',
      todo: ['表格 8 行，含向量化状态 + 进度微条（ProgressInline）', '右上「+ 创建知识库」']
    }
  },
  {
    path: 'knowledge/create',
    name: 'knowledge-create',
    component: Stub,
    meta: {
      title: '创建新知识库',
      module: '知识库',
      navKey: 'knowledge',
      skeleton: 'E',
      phase: 'P7',
      screen: '05-知识库-创建.png',
      todo: [
        '单列纵向表单（字段拉通整行），5 个字段',
        '左下主按钮；分块大小 800 / 重叠 150 的默认值'
      ]
    }
  },
  {
    path: 'knowledge/:id/detail',
    name: 'knowledge-detail',
    component: () => import('@/views/knowledge/KnowledgeDetailView.vue'),
    meta: {
      title: '知识库详情',
      module: '知识库',
      navKey: 'knowledge',
      skeleton: 'C',
      phase: 'P6',
      screen: '05-知识库-FAQ知识库.png',
      todo: [
        '左信息卡 + 右快速操作卡',
        '向量化进度条（65% 处理中态）',
        '技术文档库页面状态值为空，必须兜底「未知」'
      ]
    }
  },

  // ================= Agent =================
  {
    path: 'agent/list',
    name: 'agent-list',
    component: () => import('@/views/agent/AgentListView.vue'),
    meta: {
      title: 'AI Agent',
      module: 'Agent',
      navKey: 'agent',
      skeleton: 'A1',
      phase: 'P5',
      screen: '06-AI Agent.png',
      todo: [
        '表格 7 列 ×8 行（单列圆角卡包裹）',
        '策略徽章：Function Calling / ReAct / Chain of Thought',
        '右上「+ 创建 Agent」'
      ]
    }
  },
  {
    path: 'agent/create',
    name: 'agent-create',
    component: Stub,
    meta: {
      title: '创建新Agent',
      module: 'Agent',
      navKey: 'agent',
      skeleton: 'E',
      phase: 'P7',
      screen: '06-Agent-创建.png',
      todo: [
        '页头含「测试 / 保存」',
        '两栏表单：主表单 2/3 + 高级配置 1/3',
        '工具多选卡片（AppSelectCard）+ 知识库绑定'
      ]
    }
  },
  {
    path: 'agent/:id/detail',
    name: 'agent-detail',
    component: () => import('@/views/agent/AgentDetailView.vue'),
    meta: {
      title: 'Agent 详情',
      module: 'Agent',
      navKey: 'agent',
      skeleton: 'C',
      phase: 'P6',
      screen: '06-智能客服助手.png',
      todo: [
        '页头：返回 + 头像 + 标题 + 状态徽章 + 运行/复制/分享/编辑',
        '3 个 Tab：配置 / 运行历史 / 工具管理（后两个原型未画，需补）',
        '左：基本信息 + 系统提示词；右：统计信息 + 删除 Agent',
        '7 份数据实例共用此模板，状态分支 活跃/草稿/暂停/错误 必须全覆盖'
      ]
    }
  },

  // ================= 提示词工程 =================
  {
    path: 'prompt/list',
    name: 'prompt-list',
    component: () => import('@/views/prompt/PromptListView.vue'),
    meta: {
      title: '提示词管理',
      module: '提示词工程',
      navKey: 'prompt',
      skeleton: 'A1',
      phase: 'P5',
      screen: '07-提示词管理.png',
      todo: ['全宽表格 7 列 ×8 行，无分页（需补分页）', '行内 ▶ 进入编辑器']
    }
  },
  {
    path: 'prompt/create',
    name: 'prompt-create',
    component: Stub,
    meta: {
      title: '创建新提示词',
      module: '提示词工程',
      navKey: 'prompt',
      skeleton: 'B',
      phase: 'P7',
      screen: '07-创建新提示词.png',
      todo: ['居中标题区 + 三列卡片网格（8 卡，含空白卡）']
    }
  },
  {
    path: 'prompt/:id/edit',
    name: 'prompt-edit',
    component: Stub,
    meta: {
      title: '提示词编辑器',
      module: '提示词工程',
      navKey: 'prompt',
      skeleton: 'E',
      phase: 'P9',
      screen: '07-智能聊天助手.png',
      todo: [
        '内容头：运行 / 保存 / 设置 / 历史 / 分享',
        'Tab：提示词编辑 / 变量管理 / 模型配置（后两个原型未画）',
        '左 CodeEditor + 右测试运行面板（含流式）'
      ]
    }
  },

  // ================= LLMOps =================
  {
    path: 'llmops/overview',
    name: 'llmops-overview',
    component: Stub,
    meta: {
      title: 'LLMOps 运维中心',
      module: 'LLMOps监控',
      navKey: 'llmops',
      skeleton: 'A2',
      phase: 'P10',
      screen: '08-LLMOps监控-概览.png',
      todo: [
        '5 个 Tab：概览/模型监控/成本管理/AB测试/安全合规',
        '6 个统计卡 + 左右双列（健康状态 + 告警）',
        '?alerts=1 告警中心弹窗、?settings=1 设置弹窗'
      ]
    }
  },
  {
    path: 'llmops/models',
    name: 'llmops-models',
    component: Stub,
    meta: {
      title: '模型性能监控',
      module: 'LLMOps监控',
      navKey: 'llmops',
      skeleton: 'A2',
      phase: 'P10',
      screen: '08-LLM-模型监控.png',
      todo: ['卡头含时间范围 + 刷新', '8 列表格']
    }
  },
  {
    path: 'llmops/cost',
    name: 'llmops-cost',
    component: Stub,
    meta: {
      title: '成本分析管理',
      module: 'LLMOps监控',
      navKey: 'llmops',
      skeleton: 'A2',
      phase: 'P10',
      screen: '08-LLM-成本管理.png',
      todo: ['左折线图（ECharts，系列色 #1976D2）+ 右预算设置', '金额用等宽字体']
    }
  },
  {
    path: 'llmops/ab-test',
    name: 'llmops-ab-test',
    component: Stub,
    meta: {
      title: 'A/B 测试管理',
      module: 'LLMOps监控',
      navKey: 'llmops',
      skeleton: 'A2',
      phase: 'P10',
      screen: '08-LLM-AB测试.png',
      todo: ['卡头「创建新测试」（弹窗原型未画，需补）', '7 列表格']
    }
  },
  {
    path: 'llmops/security',
    name: 'llmops-security',
    component: Stub,
    meta: {
      title: '安全合规',
      module: 'LLMOps监控',
      navKey: 'llmops',
      skeleton: 'A2',
      phase: 'P10',
      screen: '08-LLM-安全合规.png',
      todo: ['双栏：安全监控/合规检查 + 访问日志/安全设置']
    }
  },

  // ================= 插件市场 =================
  {
    path: 'plugin/market',
    name: 'plugin-market',
    component: Stub,
    meta: {
      title: '插件市场',
      module: '插件市场',
      navKey: 'plugin',
      skeleton: 'B',
      phase: 'P8',
      screen: '09-插件市场.png',
      todo: [
        '搜索 + 分类 + 排序条 + 分类 chips + 4 列卡片网格',
        '插件卡：图标/认证标/星级/价格/安装按钮',
        '插件详情页原型未画，需补'
      ]
    }
  },

  // ================= 数据集 =================
  {
    path: 'dataset/list',
    name: 'dataset-list',
    component: () => import('@/views/dataset/DatasetListView.vue'),
    meta: {
      title: '数据集管理',
      module: '数据集',
      navKey: 'dataset',
      skeleton: 'A1',
      phase: 'P5',
      screen: '10-数据集管理.png',
      todo: [
        '表格 7 列 ×8 行，含类型/状态/进度',
        '「最后更新」列实际渲染的是进度条，需显式拆出「进度」列',
        '注意：数据集 ≠ 知识库，不可共用实体与 store'
      ]
    }
  },
  {
    path: 'dataset/:id/detail',
    name: 'dataset-detail',
    component: () => import('@/views/dataset/DatasetDetailView.vue'),
    meta: {
      title: '数据集详情',
      module: '数据集',
      navKey: 'dataset',
      skeleton: 'C',
      phase: 'P6',
      screen: '10-数据集-产品知识库.png',
      todo: ['左信息卡 4 字段 + 右操作卡', '创建时间字段为空，必须兜底为 -']
    }
  },

  // ================= 工具 =================
  {
    path: 'tool/list',
    name: 'tool-list',
    component: () => import('@/views/tool/ToolListView.vue'),
    meta: {
      title: '工具',
      module: '工具',
      navKey: 'tool',
      skeleton: 'A1',
      phase: 'P5',
      screen: '11-工具.png',
      todo: [
        '卡片包裹全宽表格 6 列 ×10 行',
        'orange 整行 hover（--color-accent-soft）',
        '右上「+ 创建工具」'
      ]
    }
  },
  {
    path: 'tool/create',
    name: 'tool-create',
    component: Stub,
    meta: {
      title: '创建工具',
      module: '工具',
      navKey: 'tool',
      skeleton: 'E',
      phase: 'P7',
      screen: '11-工具-创建工具.png',
      todo: [
        '原型此页标题与字段全英文（Create New Tool），需中文化',
        '单列 4 字段表单',
        '输入参数需拆分 inputParams(自然语言) + inputSchema(逗号分隔)'
      ]
    }
  },
  {
    path: 'tool/:id/detail',
    name: 'tool-detail',
    component: () => import('@/views/tool/ToolDetailView.vue'),
    meta: {
      title: '工具详情',
      module: '工具',
      navKey: 'tool',
      skeleton: 'C',
      phase: 'P6',
      screen: '11-工具-文本摘要器.png',
      todo: ['左只读信息卡 4 字段 + 右操作卡 4 按钮', '运行工具原型未画，复用 RunTestPanel']
    }
  },
  {
    path: 'tool/template/config',
    name: 'tool-template-config',
    component: Stub,
    meta: {
      title: '配置模板: 工具模板',
      module: '工具',
      navKey: 'tool',
      skeleton: 'E',
      phase: 'P7',
      screen: '11-配置模板-工具模板.png',
      todo: ['居中窄栏 ≈600px：说明卡 + 2×2 模板配置卡']
    }
  },

  // ================= 模型厂商 =================
  {
    path: 'providers',
    name: 'providers',
    component: () => import('@/views/providers/ProviderListView.vue'),
    meta: {
      title: '模型提供商',
      module: '模型厂商',
      navKey: 'providers',
      skeleton: 'A2',
      phase: 'P6',
      screen: '12-模型提供商.png',
      todo: [
        '4 个 Tab：所有提供商 / 已配置 / 可用模型 / 调用统计',
        '三列两行 6 个厂商卡（含开关与配置/重新配置）',
        'Azure OpenAI 卡为红色错误态'
      ]
    }
  },
  {
    path: 'providers/:id',
    name: 'provider-detail',
    component: () => import('@/views/providers/ProviderDetailView.vue'),
    meta: {
      title: '模型厂商详情',
      module: '模型厂商',
      navKey: 'providers',
      skeleton: 'C',
      phase: 'P6',
      screen: '12-模型-AWS Bedrock.png',
      todo: [
        '左只读信息卡：API 密钥 / 可用模型 / 状态 / 创建时间 + 右操作卡 4 按钮',
        '4 份数据实例共用（AWS/Azure/Google/Hugging Face）',
        '「API 密钥」原被截断成「API 密」，按完整文案实现'
      ]
    }
  }
]

/** 登录页（无壳） */
const loginRoute: RouteRecordRaw = {
  path: '/login',
  name: 'login',
  component: () => import('@/views/auth/LoginView.vue'),
  meta: {
    title: '登录',
    module: '登录',
    skeleton: 'L0',
    phase: 'P11',
    blank: true,
    screen: '01-登录.png'
  }
}

export const routes: RouteRecordRaw[] = [
  loginRoute,
  {
    path: '/',
    component: () => import('@/app/layouts/AppShell.vue'),
    children: [
      { path: '', redirect: '/explore' },
      ...shellRoutes,
      // 未匹配的兜底到探索页，避免开发时白屏
      { path: ':pathMatch(.*)*', redirect: '/explore' }
    ]
  }
]
