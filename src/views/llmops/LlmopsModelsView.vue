<script setup lang="ts">
import { computed } from 'vue'
import {
  AppButton,
  AppContentCard,
  AppDataTable,
  AppStatusBadge
} from '@/components/ui'
import type { TableColumn } from '@/components/ui'
import EChart from '@/components/charts/EChart.vue'
import { getModelPerf } from '@/api/llmops'
import { useResource } from '@/composables/useResource'
import { formatNumber } from '@/utils/format'

/**
 * 模型性能监控（原型 08-LLM-模型监控.png）。
 * 原型是「卡头带时间范围 + 刷新」+ 8 列表格；这里补一个调用量柱状图，表格保留。
 */
const { data: rows, loading, reload } = useResource(getModelPerf)

const columns: TableColumn[] = [
  { key: 'model', title: '模型', width: '22%', emphasis: true, ellipsis: true },
  { key: 'calls', title: '调用次数', width: '12%', align: 'right', sortable: true },
  { key: 'successRate', title: '成功率', width: '12%', align: 'right' },
  { key: 'avgLatencyMs', title: '平均延迟', width: '14%', align: 'right' },
  { key: 'totalTokens', title: 'Token 数', width: '16%', align: 'right' },
  { key: 'totalCostUsd', title: '成本', width: '14%', align: 'right' }
]

const tableRows = computed(() =>
  (rows.value ?? []).map((row) => ({
    ...row,
    successRate: `${row.successRate}%`,
    avgLatencyMs: `${formatNumber(row.avgLatencyMs)} ms`,
    totalTokens: formatNumber(row.totalTokens),
    totalCostUsd: `$${row.totalCostUsd.toFixed(2)}`
  }))
)

const barOption = computed(() => {
  const list = rows.value ?? []
  return {
    grid: { left: 4, right: 12, top: 20, bottom: 4, containLabel: true },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: list.map((row) => row.model),
      axisLine: { lineStyle: { color: '#E8E3E7' } },
      axisTick: { show: false },
      axisLabel: { color: '#9E9E9E', fontSize: 11, interval: 0, rotate: list.length > 4 ? 12 : 0 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#F3EDF7' } },
      axisLabel: { color: '#9E9E9E', fontSize: 11 }
    },
    series: [
      {
        name: '调用次数',
        type: 'bar',
        barWidth: '46%',
        itemStyle: { color: '#6750A4', borderRadius: [6, 6, 0, 0] },
        data: list.map((row) => row.calls)
      }
    ]
  }
})
</script>

<template>
  <div class="models">
    <AppContentCard title="调用量分布" subtitle="同一批 traces，按模型聚合">
      <EChart :option="barOption" :height="220" :loading="loading" />
    </AppContentCard>

    <AppContentCard title="模型性能明细" subtitle="卡头时间范围与刷新：当前为全量 15 天" flush>
      <template #actions>
        <AppButton size="sm" variant="secondary" icon="mdi-refresh" :loading="loading" @click="reload">
          刷新
        </AppButton>
      </template>
      <AppDataTable
        :columns="columns"
        :rows="tableRows"
        :loading="loading"
        empty-title="还没有调用记录"
        empty-description="跑一次工作流或提示词测试就会产生 trace"
      >
        <template #cell-successRate="{ row }">
          <AppStatusBadge
            :status="String(row.successRate)"
            :tone="Number(String(row.successRate).replace('%', '')) >= 95 ? 'success' : 'warning'"
            variant="text"
          />
        </template>
      </AppDataTable>
    </AppContentCard>
  </div>
</template>

<style scoped>
.models {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  padding-bottom: var(--spacing-6);
}
</style>
