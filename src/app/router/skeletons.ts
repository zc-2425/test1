/** 页面骨架类型，对应 docs/03-组件与模式清单.md §6 的八种配方 */
export type SkeletonKind = 'A1' | 'A2' | 'B' | 'C' | 'D' | 'E' | 'F' | 'L0'

export interface SkeletonMeta {
  /** 配方名 */
  name: string
  /** 组装顺序 */
  recipe: string
}

export const SKELETONS: Record<SkeletonKind, SkeletonMeta> = {
  A1: {
    name: '列表页（右上主按钮）',
    recipe: 'AppShell → PageHeader(标题+副标题+右上主按钮) → ContentCard → AppDataTable / 分页'
  },
  A2: {
    name: '列表页（卡片包裹 + Tab）',
    recipe: 'AppShell → PageHeader(含操作组) → TabNav → ContentCard → AppDataTable'
  },
  B: {
    name: '模板/卡片网格页',
    recipe: 'AppShell → PageHeader → FilterBar(搜索+分类 chips+排序) → 卡片网格(TemplateCard)'
  },
  C: {
    name: '详情页（左右分栏）',
    recipe: 'AppShell → DetailHeader(返回+图标+标题+状态+操作组) → TabNav → 左信息卡 / 右操作卡'
  },
  D: {
    name: '画布页（无侧栏三栏）',
    recipe: 'CanvasLayout(顶栏+工具栏) → 节点库(10) / 点阵画布 / 节点属性面板'
  },
  E: {
    name: '编辑器/创建页',
    recipe: 'AppShell → 内容头(运行/保存) → TabNav → 左编辑器 / 右测试运行 或 两栏表单'
  },
  F: {
    name: '弹窗/向导（叠在父页之上）',
    recipe: 'AppModal(居中+遮罩) → 表单；由父路由的 query 控制显隐'
  },
  L0: {
    name: '无壳全屏',
    recipe: 'AuthLayout(紫蓝渐变 + 居中卡片)'
  }
}
