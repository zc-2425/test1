/**
 * 侧边栏导航定义 —— 唯一事实来源。
 * 62 张截图里侧栏结构完全一致：11 项一级菜单平铺，无分组标题、无二级、无折叠。
 * 顺序固定（docs/02-信息架构.md §一）。
 */
export interface NavItem {
  /** 高亮键，路由 meta.navKey 与之匹配 */
  key: string
  label: string
  /** MDI 图标类名 */
  icon: string
  to: string
}

export const NAV_ITEMS: NavItem[] = [
  { key: 'explore', label: '探索', icon: 'mdi-compass-outline', to: '/explore' },
  { key: 'workflow', label: '工作流', icon: 'mdi-sitemap-outline', to: '/workflow/list' },
  { key: 'app', label: '应用中心', icon: 'mdi-view-grid-outline', to: '/app/list' },
  {
    key: 'knowledge',
    label: '知识库',
    icon: 'mdi-book-open-page-variant-outline',
    to: '/knowledge/list'
  },
  { key: 'agent', label: 'Agent', icon: 'mdi-robot-outline', to: '/agent/list' },
  { key: 'prompt', label: '提示词工程', icon: 'mdi-code-tags', to: '/prompt/list' },
  { key: 'llmops', label: 'LLMOps监控', icon: 'mdi-monitor-dashboard', to: '/llmops/overview' },
  { key: 'plugin', label: '插件市场', icon: 'mdi-star-outline', to: '/plugin/market' },
  { key: 'dataset', label: '数据集', icon: 'mdi-database-outline', to: '/dataset/list' },
  { key: 'tool', label: '工具', icon: 'mdi-wrench-outline', to: '/tool/list' },
  { key: 'providers', label: '模型厂商', icon: 'mdi-atom', to: '/providers' }
]
