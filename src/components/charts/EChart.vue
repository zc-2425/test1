<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TooltipComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

/**
 * ECharts 薄封装。
 *
 * 按需注册（只引 line/bar/pie + 需要的组件），比整包少一半以上体积。
 * 容器尺寸变化用 ResizeObserver 跟着 resize；组件卸载时 dispose，避免实例泄漏。
 */
echarts.use([
  LineChart,
  BarChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
  CanvasRenderer
])

const props = withDefaults(
  defineProps<{
    option: Record<string, unknown>
    height?: number | string
    /** 数据加载中显示骨架 */
    loading?: boolean
  }>(),
  { height: 260, loading: false }
)

const container = ref<HTMLElement | null>(null)
const chart = shallowRef<echarts.ECharts | null>(null)
let observer: ResizeObserver | null = null

function render(): void {
  if (!container.value) return
  if (!chart.value) {
    chart.value = echarts.init(container.value, undefined, { renderer: 'canvas' })
  }
  chart.value.setOption(props.option, true)
}

onMounted(() => {
  render()
  if (container.value) {
    observer = new ResizeObserver(() => chart.value?.resize())
    observer.observe(container.value)
  }
})

watch(
  () => props.option,
  () => render(),
  { deep: true }
)

onBeforeUnmount(() => {
  observer?.disconnect()
  chart.value?.dispose()
  chart.value = null
})
</script>

<template>
  <div class="echart" :style="{ height: typeof height === 'number' ? `${height}px` : height }">
    <div v-if="loading" class="echart__loading">
      <span class="u-skeleton" v-for="i in 3" :key="i" :style="{ width: `${70 - i * 12}%` }" />
    </div>
    <div v-show="!loading" ref="container" class="echart__canvas" />
  </div>
</template>

<style scoped>
.echart {
  width: 100%;
  min-width: 0;
}

.echart__canvas {
  width: 100%;
  height: 100%;
}

.echart__loading {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  justify-content: center;
  height: 100%;
  padding: var(--spacing-4);
}
</style>
