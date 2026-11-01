<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  AppButton,
  AppContentCard,
  AppKeyValueList,
  AppProgressInline,
  AppSlider
} from '@/components/ui'
import EChart from '@/components/charts/EChart.vue'
import { getCostSeries, getOverview } from '@/api/llmops'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'

/**
 * 成本分析（原型 08-LLM-成本管理.png）。
 * 左侧按模型堆叠的每日成本折线，右侧预算卡（预算只是本地状态，后端没有预算表）。
 */
const { data: cost, loading } = useResource(() => getCostSeries(15))
const { data: overview } = useResource(getOverview)

const monthlyBudget = ref(1600)
const used = computed(() => overview.value?.cards.totalCostUsd ?? 0)
const remaining = computed(() => Math.max(0, monthlyBudget.value - used.value))
const usagePercent = computed(() =>
  monthlyBudget.value > 0 ? Math.min(100, (used.value / monthlyBudget.value) * 100) : 0
)

const PALETTE = ['#1976D2', '#6750A4', '#2E7D32', '#F57C00', '#BA1A1A']

const option = computed(() => {
  const series = cost.value?.series ?? []
  const models = cost.value?.models ?? []
  return {
    grid: { left: 4, right: 12, top: 32, bottom: 4, containLabel: true },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: number) => `$${Number(value).toFixed(3)}`
    },
    legend: {
      top: 0,
      left: 0,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#5D5A5D', fontSize: 11 }
    },
    xAxis: {
      type: 'category',
      data: series.map((point) => point.day.slice(5)),
      axisLine: { lineStyle: { color: '#E8E3E7' } },
      axisTick: { show: false },
      axisLabel: { color: '#9E9E9E', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#F3EDF7' } },
      axisLabel: { color: '#9E9E9E', fontSize: 11, formatter: '${value}' }
    },
    series: models.map((model, index) => ({
      name: model,
      type: 'line',
      stack: 'cost',
      smooth: true,
      showSymbol: false,
      areaStyle: { opacity: 0.24 },
      lineStyle: { width: 1.5, color: PALETTE[index % PALETTE.length] },
      itemStyle: { color: PALETTE[index % PALETTE.length] },
      data: series.map((point) => Number(point[model] ?? 0))
    }))
  }
})

function saveBudget(): void {
  toast('预算已更新', { tone: 'success', description: `月度预算 $${monthlyBudget.value}` })
}
</script>

<template>
  <div class="cost">
    <AppContentCard title="每日成本（按模型堆叠）" subtitle="成本 = token × 单价，逐条 trace 累加">
      <EChart :option="option" :height="320" :loading="loading" />
    </AppContentCard>

    <div class="cost__side">
      <AppContentCard title="预算" subtitle="本地设置，未接后端" dense>
        <div class="budget">
          <div class="budget__row">
            <span class="budget__used">${{ used.toFixed(2) }}</span>
            <span class="budget__of">/ ${{ monthlyBudget }}</span>
          </div>
          <AppProgressInline :value="usagePercent" :width="200" :show-label="false" />
          <p class="budget__hint">
            已用 {{ usagePercent.toFixed(1) }}% · 剩余 ${{ remaining.toFixed(2) }}
          </p>
          <AppSlider v-model="monthlyBudget" label="月度预算" :min="200" :max="5000" :step="100" suffix=" USD" />
          <AppButton size="sm" variant="secondary" @click="saveBudget">保存预算</AppButton>
        </div>
      </AppContentCard>

      <AppContentCard title="成本构成" dense>
        <AppKeyValueList
          :items="[
            { label: '总调用次数', value: overview?.cards.totalCalls ?? 0 },
            { label: '总 token', value: (overview?.cards.totalTokens ?? 0).toLocaleString('zh-CN') },
            { label: '累计成本', value: `$${(overview?.cards.totalCostUsd ?? 0).toFixed(2)}` },
            {
              label: '平均每次成本',
              value: `$${((overview?.cards.totalCostUsd ?? 0) / Math.max(1, overview?.cards.totalCalls ?? 1)).toFixed(4)}`
            }
          ]"
        />
      </AppContentCard>
    </div>
  </div>
</template>

<style scoped>
.cost {
  display: grid;
  grid-template-columns: minmax(0, 1.9fr) minmax(0, 1fr);
  gap: var(--spacing-4);
  align-items: start;
  padding-bottom: var(--spacing-6);
}

@media (max-width: 1280px) {
  .cost {
    grid-template-columns: minmax(0, 1fr);
  }
}

.cost__side {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  min-width: 0;
}

.budget {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.budget__row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.budget__used {
  font: var(--font-display-sm);
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.budget__of {
  font: var(--font-body-sm);
  color: var(--color-text-tertiary);
}

.budget__hint {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}
</style>
