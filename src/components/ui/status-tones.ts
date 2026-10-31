import type { StatusTone } from '@/types/common'

/**
 * 状态 → 色调 的唯一映射表。
 *
 * 为什么必须有这张表：原型里有 28 个状态词散落在 40 张画布上，
 * 且同一个词在不同实体上含义不同（`错误` 在 Agent=运行失败、在厂商=密钥失效）。
 * 把映射集中在这里，页面只写 <AppStatusBadge status="已发布" />，
 * 将来要改配色只改一处，不会出现「列表绿、详情灰」的自相矛盾。
 */
export const STATUS_TONES: Record<string, StatusTone> = {
  // —— 成功 / 正向 ——
  已发布: 'success',
  已完成: 'success',
  可用: 'success',
  活跃: 'success',
  已连接: 'success',
  已就绪: 'success',
  已入库: 'success',
  成功: 'success',
  已解决: 'success',
  已安装: 'success',
  已启用: 'success',

  // —— 进行中 ——
  运行中: 'running',
  处理中: 'running',
  测试中: 'running',
  解析中: 'running',
  向量化中: 'running',
  安装中: 'running',

  // —— 警告 / 中断 ——
  暂停: 'warning',
  维护中: 'warning',
  已停止: 'warning',
  警告: 'warning',
  待处理: 'warning',
  未处理: 'warning',
  待审核: 'warning',

  // —— 失败 / 危险 ——
  失败: 'danger',
  错误: 'danger',
  异常: 'danger',
  严重: 'danger',
  已停用: 'danger',

  // —— 中性 / 草稿 ——
  草稿: 'neutral',
  未连接: 'neutral',
  未安装: 'neutral',
  停用: 'neutral',
  未知: 'neutral',
  未启用: 'neutral',

  // —— 提示 ——
  提示: 'info',

  // —— 强调 ——
  推荐: 'accent',
  热门: 'accent'
}

/** 未知状态一律当中性处理，避免渲染出空白胶囊 */
export function toneOf(status: string | null | undefined): StatusTone {
  if (!status) return 'neutral'
  return STATUS_TONES[status] ?? 'neutral'
}

/** 类型标签（聊天流/工作流/文档…）不走状态色，统一中性色，和状态胶囊区分开 */
export const TYPE_CHIP_KEYS = new Set([
  '聊天流',
  '工作流',
  '文档',
  '问答对',
  '表格',
  '内置',
  '自定义API',
  '聊天机器人',
  '智能体',
  '工作流应用',
  '聊天助手',
  '内容创作',
  '销售',
  '技术支持',
  '数据分析',
  '办公'
])
