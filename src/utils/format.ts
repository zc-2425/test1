/**
 * 展示层格式化工具。
 * 放在这里而不是每个页面写一遍：列表页的「最后运行 2 小时前」「成功率 98.2%」
 * 「使用量 1,250」都是同一套规则。
 */

const MINUTE = 60_000
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

function toDate(value: string | number | Date): Date | null {
  const date = value instanceof Date ? value : new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function pad(n: number): string {
  return String(n).padStart(2, '0')
}

/** 2024-01-15 10:00 */
export function formatDateTime(
  value: string | number | Date | null | undefined,
  fallback = '-'
): string {
  if (value === null || value === undefined || value === '') return fallback
  const date = toDate(value)
  if (!date) return fallback
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

/** 2024-01-15 */
export function formatDate(value: string | number | Date | null | undefined, fallback = '-'): string {
  if (value === null || value === undefined || value === '') return fallback
  const date = toDate(value)
  if (!date) return fallback
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/** 2 小时前 / 3 天前 / 刚刚（原型列表里就是这么写的） */
export function formatRelative(
  value: string | number | Date | null | undefined,
  fallback = '从未'
): string {
  if (value === null || value === undefined || value === '') return fallback
  const date = toDate(value)
  if (!date) return fallback

  const diff = Date.now() - date.getTime()
  if (diff < 0) {
    const ahead = Math.abs(diff)
    if (ahead < HOUR) return `${Math.max(1, Math.round(ahead / MINUTE))} 分钟后`
    if (ahead < DAY) return `${Math.round(ahead / HOUR)} 小时后`
    return `${Math.round(ahead / DAY)} 天后`
  }
  if (diff < MINUTE) return '刚刚'
  if (diff < HOUR) return `${Math.round(diff / MINUTE)} 分钟前`
  if (diff < DAY) return `${Math.round(diff / HOUR)} 小时前`
  if (diff < 30 * DAY) return `${Math.round(diff / DAY)} 天前`
  return formatDate(date)
}

/** 1250 → 1,250 */
export function formatNumber(value: number | null | undefined, fallback = '-'): string {
  if (value === null || value === undefined || Number.isNaN(value)) return fallback
  return value.toLocaleString('zh-CN')
}

/** 0.982 或 98.2 → 98.2% */
export function formatPercent(value: number | null | undefined, fallback = '-'): string {
  if (value === null || value === undefined || Number.isNaN(value)) return fallback
  const normalized = value <= 1 ? value * 100 : value
  return `${normalized.toFixed(1)}%`
}

/** 传入天数，返回最近 N 天的 ISO 日期数组（LLMOps 图表用） */
export function lastNDays(n: number): string[] {
  const days: string[] = []
  for (let i = n - 1; i >= 0; i -= 1) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    days.push(`${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`)
  }
  return days
}
