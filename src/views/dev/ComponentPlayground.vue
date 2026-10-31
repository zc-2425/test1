<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  AppContentCard,
  AppDataTable,
  AppEmptyState,
  AppKeyValueList,
  AppPageHeader,
  AppPagination,
  AppProgressInline,
  AppStatCard,
  AppStatusBadge,
  AppTagChip,
  STATUS_TONES
} from '@/components/ui'
import { listWorkflows, type WorkflowDto } from '@/api/workflows'
import type { SortState, TableColumn } from '@/types/common'
import { formatRelative } from '@/utils/format'

/**
 * P3 组件预览页（仅开发用，不在 62 画布的 31 条业务路由里）。
 * 作用有两个：1) 组件视觉基线，改样式先来这里看全量；2) 用真接口验一遍前后端链路。
 */

const statusList = Object.keys(STATUS_TONES)
const variants = ['solid', 'soft', 'text'] as const

/* ---------------- 静态演示表 ---------------- */
interface DemoRow extends Record<string, unknown> {
  id: string
  name: string
  type: string
  status: string
  node_count: number
  progress: number
  cost: string
}

const demoColumns: TableColumn[] = [
  { key: 'name', title: '工作流', width: '26%', emphasis: true, ellipsis: true },
  { key: 'type', title: '类型', width: '10%', render: 'tag' },
  { key: 'status', title: '状态', width: '10%', render: 'badge' },
  { key: 'node_count', title: '节点数', width: '8%', align: 'right', sortable: true },
  { key: 'progress', title: '进度', width: '16%', render: 'progress' },
  { key: 'cost', title: '成本', width: '10%', render: 'mono', align: 'right' },
  { key: 'actions', title: '操作', width: '10%', render: 'actions', align: 'right' }
]

const demoRows: DemoRow[] = [
  { id: 'd1', name: '智能客服工作流', type: '聊天流', status: '已发布', node_count: 8, progress: 100, cost: '$0.42' },
  { id: 'd2', name: '文档摘要生成器', type: '工作流', status: '草稿', node_count: 12, progress: 0, cost: '$0.00' },
  { id: 'd3', name: '代码审查助手', type: '聊天流', status: '运行中', node_count: 15, progress: 62, cost: '$0.87' },
  { id: 'd4', name: '内容审核流程', type: '工作流', status: '失败', node_count: 7, progress: 38, cost: '$0.12' },
  { id: 'd5', name: '数据分析报告', type: '工作流', status: '待处理', node_count: 20, progress: 15, cost: '$0.03' }
]

const demoLoading = ref(false)
const demoEmpty = ref(false)

function fakeLoad(): void {
  demoLoading.value = true
  window.setTimeout(() => {
    demoLoading.value = false
  }, 1200)
}

/* ---------------- 真实接口表 ---------------- */
const columns: TableColumn[] = [
  { key: 'name', title: '工作流', width: '24%', emphasis: true, ellipsis: true },
  { key: 'type', title: '类型', width: '10%', render: 'tag' },
  { key: 'status', title: '状态', width: '10%', render: 'badge' },
  { key: 'node_count', title: '节点数', width: '9%', align: 'right', sortable: true },
  { key: 'last_run_at', title: '最后运行', width: '14%', sortable: true },
  { key: 'success_rate', title: '成功率', width: '11%', align: 'right', sortable: true },
  { key: 'created_at', title: '创建时间', width: '14%', sortable: true },
  { key: 'actions', title: '操作', width: '8%', render: 'actions', align: 'right' }
]

const rows = ref<WorkflowDto[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const keyword = ref('')
const sort = ref<SortState | null>({ key: 'created_at', order: 'desc' })
const loading = ref(false)
const error = ref<string | null>(null)
const lastClicked = ref<string>('—')

let debounceTimer: number | undefined

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const result = await listWorkflows({
      page: page.value,
      size: size.value,
      q: keyword.value || undefined,
      sort: sort.value?.key,
      order: sort.value?.order
    })
    rows.value = result.items
    total.value = result.total
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : String(cause)
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onSort(state: SortState): void {
  sort.value = state
  page.value = 1
}

watch([page, size, sort], () => void load())
watch(keyword, () => {
  window.clearTimeout(debounceTimer)
  debounceTimer = window.setTimeout(() => {
    page.value = 1
    void load()
  }, 300)
})

onMounted(() => void load())

const filtered = computed(() => keyword.value.trim().length > 0)
</script>

<template>
  <div class="kit">
    <AppPageHeader title="组件预览 · P3" subtitle="基础组件视觉基线；此处全部以真实接口数据驱动，不走写死的假数据。">
      <template #actions>
        <AppTagChip label="仅开发用" tone="warning" />
      </template>
    </AppPageHeader>

    <!-- 统计卡 -->
    <AppContentCard title="统计卡 StatCard" subtitle="探索页 4 卡（图标在上）与 LLMOps 6 卡（图标在左）">
      <div class="kit__grid kit__grid--4">
        <AppStatCard icon="mdi-view-grid-outline" :value="16" label="总模板数" tone="accent" />
        <AppStatCard icon="mdi-fire" :value="5" label="热门模板" tone="warning" />
        <AppStatCard icon="mdi-star-outline" :value="4" label="收藏模板" tone="accent" />
        <AppStatCard icon="mdi-chart-line" :value="11800" label="总使用次数" tone="success" />
      </div>
      <div class="kit__grid kit__grid--3 kit__mt">
        <AppStatCard layout="inline" icon="mdi-phone-outline" :value="932" label="总调用次数" tone="accent" />
        <AppStatCard layout="inline" icon="mdi-check-circle-outline" :value="97.2" label="成功率 %" tone="success" />
        <AppStatCard layout="inline" icon="mdi-alert-outline" :value="2" label="未处理告警" tone="danger" />
      </div>
    </AppContentCard>

    <!-- 状态胶囊 -->
    <AppContentCard title="状态胶囊 StatusBadge" subtitle="状态词 → 颜色 的唯一映射，未知状态兜底为「未知」灰胶囊">
      <div class="kit__badges">
        <div v-for="variant in variants" :key="variant" class="kit__badge-row">
          <span class="kit__row-label">{{ variant }}</span>
          <div class="kit__badge-wrap">
            <AppStatusBadge
              v-for="status in statusList"
              :key="`${variant}-${status}`"
              :status="status"
              :variant="variant"
            />
          </div>
        </div>
        <div class="kit__badge-row">
          <span class="kit__row-label">兜底</span>
          <div class="kit__badge-wrap">
            <AppStatusBadge :status="null" />
            <AppStatusBadge status="某个没登记过的新状态" />
            <AppStatusBadge status="错误" tone="danger" variant="soft" />
          </div>
        </div>
      </div>
    </AppContentCard>

    <!-- 标签与进度 -->
    <div class="kit__grid kit__grid--2">
      <AppContentCard title="胶囊标签 TagChip" subtitle="分类/类型，与状态胶囊刻意区分配色">
        <div class="kit__chips">
          <AppTagChip label="默认" />
          <AppTagChip label="强调" tone="accent" />
          <AppTagChip label="成功" tone="success" />
          <AppTagChip label="警告" tone="warning" />
          <AppTagChip label="危险" tone="danger" />
          <AppTagChip label="进行中" tone="running" />
        </div>
        <div class="kit__chips kit__mt">
          <AppTagChip label="全部" clickable active />
          <AppTagChip label="AI助手" clickable />
          <AppTagChip label="内容创作" clickable />
          <AppTagChip label="开发工具" clickable />
        </div>
      </AppContentCard>

      <AppContentCard title="细进度条 ProgressInline" subtitle="颜色随进度分档，也可强制指定">
        <div class="kit__progress">
          <AppProgressInline :value="100" />
          <AppProgressInline :value="75" />
          <AppProgressInline :value="38" />
          <AppProgressInline :value="0" />
          <AppProgressInline :value="62" tone="danger" />
        </div>
      </AppContentCard>
    </div>

    <!-- 键值列表 -->
    <div class="kit__grid kit__grid--2">
      <AppContentCard title="键值列表 KeyValueList" subtitle="详情页左信息卡；缺失值必须兜底成 -">
        <AppKeyValueList
          :columns="2"
          :items="[
            { label: 'Agent 名称', value: '智能客服助手', variant: 'strong' },
            { label: 'Agent 类型', value: '聊天助手' },
            { label: '推理策略', value: 'Function Calling' },
            { label: '创建时间', value: '2024-01-15' },
            { label: '最后运行', value: '10 分钟前' },
            { label: '丢失字段（演示兜底）', value: null }
          ]"
        />
      </AppContentCard>

      <AppContentCard title="空状态 EmptyState" subtitle="原型一次都没画过，但每个列表和详情都会遇到">
        <AppEmptyState
          icon="mdi-robot-confused-outline"
          title="还没有创建任何 Agent"
          description="从模板开始最快，或者从空白开始自定义"
        >
          <template #action>
            <v-btn color="primary" size="small" class="text-none">+ 创建第一个 Agent</v-btn>
          </template>
        </AppEmptyState>
      </AppContentCard>
    </div>

    <!-- 数据表格：静态能力演示 -->
    <AppContentCard
      title="数据表格 AppDataTable"
      subtitle="列定义驱动：text / tag / badge / progress / mono / actions 六种渲染 + 行悬停橙色"
      flush
    >
      <template #actions>
        <v-btn size="small" variant="text" class="text-none" @click="fakeLoad">模拟加载</v-btn>
        <v-btn size="small" variant="text" class="text-none" @click="demoEmpty = !demoEmpty">
          {{ demoEmpty ? '恢复数据' : '切换空态' }}
        </v-btn>
      </template>
      <AppDataTable
        :columns="demoColumns"
        :rows="demoEmpty ? [] : demoRows"
        :loading="demoLoading"
        empty-title="还没有工作流"
        empty-description="从模板创建一个，或者从空白工作流开始"
      >
        <template #actions="{ row }">
          <button type="button" class="kit__icon-btn" title="运行">
            <i class="mdi mdi-play" aria-hidden="true" />
          </button>
          <button type="button" class="kit__icon-btn" title="更多">
            <i class="mdi mdi-dots-vertical" aria-hidden="true" />
          </button>
          <span class="kit__sr">{{ row.id }}</span>
        </template>
      </AppDataTable>
    </AppContentCard>

    <!-- 数据表格：真接口 -->
    <AppContentCard title="真接口验证 · GET /api/workflows" subtitle="分页、关键字搜索、排序都走服务端；行点击可看到回调" flush>
      <template #actions>
        <span class="kit__hint">点击行：{{ lastClicked }}</span>
        <v-btn size="small" variant="text" class="text-none" :loading="loading" @click="load">刷新</v-btn>
      </template>

      <div class="kit__toolbar">
        <input v-model="keyword" class="kit__input" type="search" placeholder="搜索工作流名称…" />
        <span v-if="error" class="kit__error">{{ error }}</span>
      </div>

      <AppDataTable
        :columns="columns"
        :rows="rows"
        :loading="loading"
        clickable-rows
        :filtered="filtered"
        empty-title="还没有工作流"
        @sort="onSort"
        @row-click="(row) => (lastClicked = String(row.name))"
      >
        <template #cell-last_run_at="{ row }">
          {{ formatRelative(row.last_run_at as string | null) }}
        </template>
        <template #cell-success_rate="{ row }">
          {{ Number(row.success_rate ?? 0).toFixed(1) }}%
        </template>
        <template #cell-created_at="{ row }">
          {{ String(row.created_at ?? '').slice(0, 10) }}
        </template>
        <template #actions="{ row }">
          <button type="button" class="kit__icon-btn" title="运行" @click.stop="lastClicked = `运行 ${row.name}`">
            <i class="mdi mdi-play" aria-hidden="true" />
          </button>
          <button type="button" class="kit__icon-btn" title="更多" @click.stop>
            <i class="mdi mdi-dots-vertical" aria-hidden="true" />
          </button>
        </template>
      </AppDataTable>

      <template #footer>
        <AppPagination v-model:page="page" v-model:size="size" :total="total" />
      </template>
    </AppContentCard>
  </div>
</template>

<style scoped>
.kit {
  padding: var(--layout-page-padding);
  max-width: var(--layout-content-max);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.kit > .content-card,
.kit :deep(.content-card) {
  margin-bottom: 0;
}

.kit__grid {
  display: grid;
  gap: var(--spacing-4);
}

.kit__grid--2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.kit__grid--3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.kit__grid--4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

@media (max-width: 1280px) {
  .kit__grid--4 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.kit__mt {
  margin-top: var(--spacing-4);
}

.kit__badges {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.kit__badge-row {
  display: flex;
  gap: var(--spacing-4);
  align-items: flex-start;
}

.kit__row-label {
  flex: 0 0 56px;
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  padding-top: 4px;
}

.kit__badge-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.kit__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.kit__progress {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.kit__icon-btn {
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 18px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.kit__icon-btn:hover {
  background: var(--color-surface-container);
  color: var(--color-primary);
}

.kit__sr {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

.kit__toolbar {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: var(--border-width) solid var(--color-divider);
}

.kit__input {
  width: 260px;
  height: 34px;
  padding: 0 var(--spacing-3);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 13px;
}

.kit__input:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: -1px;
}

.kit__hint {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.kit__error {
  font: var(--font-label-sm);
  color: var(--status-danger);
}
</style>
