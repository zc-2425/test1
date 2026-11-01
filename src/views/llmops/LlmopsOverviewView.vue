<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppEmptyState,
  AppStatCard,
  AppStatusBadge,
  AppTagChip
} from '@/components/ui'
import EChart from '@/components/charts/EChart.vue'
import { getCostSeries, getOverview } from '@/api/llmops'
import { useResource } from '@/composables/useResource'
import { formatDateTime, formatNumber } from '@/utils/format'

/**
 * LLMOps 概览（原型 08-LLMOps监控-概览.png）。
 * 6 个指标卡 + 成本趋势 + 渠道健康 + 最近告警。
 */
const router = useRouter()
const { data: overview, loading } = useResource(getOverview)
const { data: cost } = useResource(() => getCostSeries(15))

const trendOption = computed(() => {
  const points = cost.value?.series ?? []
  return {
    grid: { left: 4, right: 12, top: 20, bottom: 4, containLabel: true },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: number) => `$${Number(value).toFixed(3)}`
    },
    xAxis: {
      type: 'category',
      data: points.map((point) => point.day.slice(5)),
      axisLine: { lineStyle: { color: '#E8E3E7' } },
      axisTick: { show: false },
      axisLabel: { color: '#9E9E9E', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#F3EDF7' } },
      axisLabel: { color: '#9E9E9E', fontSize: 11, formatter: '${value}' }
    },
    series: [
      {
        name: '每日成本',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: points.map((point) => point.total),
        lineStyle: { color: '#1976D2', width: 2 },
        areaStyle: { color: 'rgba(162, 210, 254, 0.35)' }
      }
    ]
  }
})

const cards = computed(() => overview.value?.cards)
</script>

<template>
  <div class="llmops">
    <div class="llmops__cards">
      <AppStatCard layout="inline" icon="mdi-phone-outline" :value="cards?.totalCalls ?? 0" label="总调用次数" tone="accent" />
      <AppStatCard layout="inline" icon="mdi-check-circle-outline" :value="cards?.successRate ?? 0" label="成功率 %" tone="success" />
      <AppStatCard layout="inline" icon="mdi-timer-outline" :value="cards?.avgLatencyMs ?? 0" label="平均延迟 ms" tone="running" />
      <AppStatCard layout="inline" icon="mdi-currency-usd" :value="`$${(cards?.totalCostUsd ?? 0).toFixed(2)}`" label="累计成本" tone="warning" />
      <AppStatCard layout="inline" icon="mdi-chart-donut" :value="cards?.totalTokens ?? 0" label="总 token" tone="info" />
      <AppStatCard layout="inline" icon="mdi-alert-outline" :value="cards?.activeAlerts ?? 0" label="未处理告警" tone="danger" />
    </div>

    <div class="llmops__grid">
      <AppContentCard title="成本趋势" subtitle="按天汇总，数据来自 traces 表">
        <EChart :option="trendOption" :height="264" :loading="!cost" />
      </AppContentCard>

      <AppContentCard title="渠道健康" subtitle="按提供商聚合" dense>
        <div v-if="loading" class="u-skeleton-stack">
          <span class="u-skeleton" v-for="i in 4" :key="i" :style="{ width: `${70 - i * 8}%` }" />
        </div>
        <ul v-else class="health">
          <li v-for="item in overview?.health ?? []" :key="item.id" class="health__item">
            <span class="health__name">{{ item.name }}</span>
            <span class="health__models">{{ item.modelCount }} 模型</span>
            <AppStatusBadge :status="item.status" variant="soft" />
          </li>
        </ul>
      </AppContentCard>
    </div>

    <AppContentCard title="最近告警" subtitle="与「告警中心」同源" flush>
      <template #actions>
        <AppButton size="sm" variant="ghost" @click="router.push({ query: { alerts: '1' } })">
          查看全部
        </AppButton>
      </template>
      <div v-if="overview?.recentAlerts.length" class="recent">
        <div v-for="alert in overview.recentAlerts" :key="alert.id" class="recent__item">
          <AppStatusBadge :status="alert.severity" variant="soft" />
          <div class="recent__body">
            <p class="recent__title">{{ alert.title }}</p>
            <p class="recent__detail">{{ alert.detail }}</p>
          </div>
          <span class="recent__time">{{ formatDateTime(alert.created_at) }}</span>
          <AppTagChip :label="alert.status" :tone="alert.status === '未处理' ? 'warning' : 'success'" />
        </div>
      </div>
      <AppEmptyState v-else size="sm" icon="mdi-bell-check-outline" title="没有未处理告警" />
    </AppContentCard>

    <p class="llmops__foot">
      统计口径：成功率 = 成功 trace 数 / 总数；成本 = Σ(token × 单价)；token 来自 prompt + completion。
      共 {{ formatNumber(cards?.totalTokens ?? 0) }} token 参与计算。
    </p>
  </div>
</template>

<style scoped>
.llmops {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.llmops__cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-3);
}

@media (max-width: 1280px) {
  .llmops__cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.llmops__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  gap: var(--spacing-4);
  align-items: start;
}

@media (max-width: 1280px) {
  .llmops__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

.health {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.health__item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: 6px 0;
  border-bottom: var(--border-width) solid var(--color-divider);
}

.health__item:last-child {
  border-bottom: 0;
}

.health__name {
  flex: 1 1 auto;
  font: var(--font-body-md);
  color: var(--color-text);
}

.health__models {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.recent {
  display: flex;
  flex-direction: column;
}

.recent__item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: var(--border-width) solid var(--color-divider);
}

.recent__item:last-child {
  border-bottom: 0;
}

.recent__body {
  flex: 1 1 auto;
  min-width: 0;
}

.recent__title {
  font: var(--font-body-md);
  color: var(--color-text);
}

.recent__detail {
  font: var(--font-body-sm);
  color: var(--color-text-secondary);
}

.recent__time {
  flex: 0 0 auto;
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.llmops__foot {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  padding-bottom: var(--spacing-6);
}
</style>
