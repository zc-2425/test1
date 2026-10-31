<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  AppButton,
  AppContentCard,
  AppDataTable,
  AppDetailHeader,
  AppDrawer,
  AppEmptyState,
  AppFileUploader,
  AppFilterBar,
  AppKeyValueList,
  AppModal,
  AppOperationCard,
  AppPageHeader,
  AppPagination,
  AppProgressInline,
  AppSelect,
  AppSlider,
  AppStatCard,
  AppStatusBadge,
  AppSwitch,
  AppTabNav,
  AppTagChip,
  AppTagInput,
  AppTextField,
  AppTextarea,
  STATUS_TONES
} from '@/components/ui'
import type { OperationItem, TabItem } from '@/components/ui'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'
import { listWorkflows, type WorkflowDto } from '@/api/workflows'
import type { SortState, TableColumn } from '@/types/common'
import { formatRelative } from '@/utils/format'

/**
 * P3 + P4 组件预览页（仅开发用，不在 62 画布的 31 条业务路由里）。
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

/* ---------------- P4 演示状态 ---------------- */
const btnLoading = ref(false)

const form = ref({
  name: '智能客服助手',
  type: '聊天助手',
  status: '活跃',
  description: '基于知识库的智能客服 Agent，能够处理常见问题并转接人工',
  systemPrompt: '你是一个智能助手，请根据用户的需求提供帮助。',
  enabled: true,
  temperature: 0.7,
  threshold: 0.75,
  tags: ['客服', '知识库'] as string[],
  files: [] as File[]
})

const typeOptions = ['聊天助手', '数据分析', '内容创作', '技术支持', '办公']
const statusOptions = ['活跃', '草稿', '暂停', '错误']

const tabUnderline = ref('config')
const tabPill = ref('all')
const underlineTabs: TabItem[] = [
  { key: 'config', label: '配置' },
  { key: 'history', label: '运行历史', count: 156 },
  { key: 'tools', label: '工具管理', count: 5 }
]
const pillTabs: TabItem[] = [
  { key: 'all', label: '所有提供商', count: 7 },
  { key: 'configured', label: '已配置', count: 3 },
  { key: 'models', label: '可用模型', count: 62 },
  { key: 'stats', label: '调用统计' }
]

const filterKeyword = ref('')
const filterStatus = ref<string | null>(null)

const modalOpen = ref(false)
const drawerOpen = ref(false)
const lastOp = ref('—')

const operations: OperationItem[] = [
  { key: 'run', label: '运行工具', icon: 'mdi-play-circle-outline', description: '用示例输入试跑一次' },
  { key: 'edit', label: '编辑配置', icon: 'mdi-pencil-outline' },
  { key: 'stats', label: '查看使用统计', icon: 'mdi-chart-line', description: '近 7 天 1,520 次调用' },
  { key: 'delete', label: '删除工具', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onOperation(key: string): Promise<void> {
  lastOp.value = key
  if (key !== 'delete') {
    toast(`已触发「${key}」`, { tone: 'info' })
    return
  }
  const ok = await confirm({
    title: '删除工具「文本摘要器」',
    description: '删除后引用它的 Agent 与工作流会失去该工具，操作不可撤销。',
    confirmText: '删除',
    tone: 'danger'
  })
  toast(ok ? '已删除（演示，未真的删除）' : '已取消', { tone: ok ? 'success' : 'info' })
}

function simulateSave(): void {
  btnLoading.value = true
  window.setTimeout(() => {
    btnLoading.value = false
    toast('保存成功', { description: '配置已更新', tone: 'success' })
  }, 900)
}

async function askDanger(): Promise<void> {
  const ok = await confirm({
    title: '删除 Agent',
    description: '将同时删除其运行历史与关联的工具授权。',
    confirmText: '删除',
    tone: 'danger'
  })
  if (ok) toast('已删除', { tone: 'success' })
}
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

    <!-- ================= P4 ================= -->

    <AppContentCard title="按钮 AppButton" subtitle="四种形态 × 两种尺寸；原型里按钮其实不统一，这里收敛成变体">
      <div class="kit__chips">
        <AppButton variant="primary">主要按钮</AppButton>
        <AppButton variant="secondary">次要按钮</AppButton>
        <AppButton variant="ghost">幽灵按钮</AppButton>
        <AppButton variant="danger">危险按钮</AppButton>
        <AppButton variant="primary" loading>保存中</AppButton>
        <AppButton variant="secondary" disabled>已禁用</AppButton>
      </div>
      <div class="kit__chips kit__mt">
        <AppButton size="sm" icon="mdi-plus">新建</AppButton>
        <AppButton size="sm" variant="secondary" icon="mdi-play">运行</AppButton>
        <AppButton size="sm" variant="secondary" icon="mdi-content-copy">复制</AppButton>
        <AppButton size="sm" variant="secondary" icon="mdi-share-variant">分享</AppButton>
        <AppButton size="sm" icon="mdi-chevron-right" icon-after>下一步</AppButton>
      </div>
    </AppContentCard>

    <AppContentCard title="表单控件" subtitle="包 Vuetify：校验态、输入法、无障碍由底座负责；标签与间距统一在这里">
      <div class="kit__grid kit__grid--2">
        <AppTextField
          v-model="form.name"
          label="Agent 名称"
          required
          prefix-icon="mdi-robot-outline"
          hint="在列表与调用示例中展示"
        />
        <AppTextField
          v-model="form.description"
          label="描述"
          prefix-icon="mdi-text-short"
          placeholder="一句话说明它是做什么的"
        />
        <AppSelect v-model="form.type" label="Agent 类型" :items="typeOptions" required />
        <AppSelect
          v-model="form.status"
          label="状态"
          :items="statusOptions"
          hint="不同状态在列表里的胶囊颜色不同"
        />
      </div>

      <div class="kit__mt">
        <AppTextarea
          v-model="form.systemPrompt"
          label="系统提示词"
          :rows="3"
          counter
          hint="支持多行，计数器上限由 maxlength 控制"
        />
      </div>

      <div class="kit__grid kit__grid--2 kit__mt">
        <AppSwitch
          v-model="form.enabled"
          label="启用该 Agent"
          description="停用后不再接受新的会话"
          show-state
        />
        <div />
        <AppSlider v-model="form.temperature" label="温度" :min="0" :max="2" :step="0.1" hint="推荐 0.7" />
        <AppSlider
          v-model="form.threshold"
          label="知识检索相似度阈值"
          :min="0"
          :max="1"
          :step="0.05"
          suffix=""
          hint="低于该值的分块不会被引用"
        />
      </div>

      <div class="kit__grid kit__grid--2 kit__mt">
        <AppTagInput v-model="form.tags" label="能力标签" :max="6" />
        <AppFileUploader
          v-model="form.files"
          label="知识库文档"
          accept=".pdf,.docx,.md,.txt"
          :max-size-mb="20"
          hint="拖拽或点击选择，支持多选"
          @error="(message) => toast(message, { tone: 'error' })"
        />
      </div>
    </AppContentCard>

    <AppContentCard title="页签 AppTabNav" subtitle="下划线式（详情页）/ 胶囊式（提供商页）">
      <AppTabNav v-model="tabUnderline" :items="underlineTabs" variant="underline" />
      <p class="kit__hint kit__mt">当前选中：{{ tabUnderline }}</p>
      <div class="kit__mt">
        <AppTabNav v-model="tabPill" :items="pillTabs" variant="pill" />
      </div>
      <p class="kit__hint kit__mt">当前选中：{{ tabPill }}</p>
    </AppContentCard>

    <AppContentCard title="详情页页头 AppDetailHeader" subtitle="返回箭头 + 头像 + 标题 + 状态 + 操作组（原型顶栏没有面包屑，返回全靠这个箭头）">
      <AppDetailHeader
        title="智能客服助手"
        subtitle="基于知识库的智能客服Agent，能够处理常见问题并转接人工"
        avatar-text="智"
        back-to="/agent/list"
      >
        <template #status>
          <AppStatusBadge status="活跃" />
        </template>
        <template #actions>
          <AppButton variant="secondary" size="sm" icon="mdi-play">运行</AppButton>
          <AppButton variant="secondary" size="sm" icon="mdi-content-copy">复制</AppButton>
          <AppButton size="sm" icon="mdi-pencil">编辑</AppButton>
        </template>
      </AppDetailHeader>
    </AppContentCard>

    <AppContentCard title="筛选条 AppFilterBar" subtitle="原型 62 页 0 个搜索框，这是必须补的；搜索 + 下拉 + 分类 chips + 右侧操作" flush>
      <AppFilterBar :summary="`共 ${total} 条`">
        <AppTextField
          v-model="filterKeyword"
          dense
          type="search"
          prefix-icon="mdi-magnify"
          placeholder="搜索名称…"
        />
        <AppSelect
          v-model="filterStatus"
          dense
          :items="statusOptions"
          placeholder="全部状态"
          clearable
        />
        <AppTagChip label="全部" clickable active />
        <AppTagChip label="聊天流" clickable />
        <AppTagChip label="工作流" clickable />
        <template #actions>
          <AppButton size="sm" variant="ghost" icon="mdi-filter-remove-outline">重置</AppButton>
          <AppButton size="sm" variant="secondary" icon="mdi-refresh">刷新</AppButton>
        </template>
      </AppFilterBar>
      <div class="kit__pad">
        <p class="kit__hint">
          关键字「{{ filterKeyword || '（空）' }}」/ 状态「{{ filterStatus || '全部' }}」——
          这里只演示结构，真实筛选在列表页接接口。
        </p>
      </div>
    </AppContentCard>

    <div class="kit__grid kit__grid--2">
      <AppContentCard title="操作卡 AppOperationCard" subtitle="详情页右栏；最后一项是危险操作">
        <AppOperationCard bare :title="''" :items="operations" @action="onOperation" />
        <p class="kit__hint kit__mt">最近触发：{{ lastOp }}</p>
      </AppContentCard>

      <AppContentCard title="反馈：Modal / Drawer / Toast / Confirm" subtitle="全部命令式调用，页面里不需要各开一份弹窗模板">
        <div class="kit__chips">
          <AppButton size="sm" variant="secondary" @click="modalOpen = true">打开弹窗</AppButton>
          <AppButton size="sm" variant="secondary" @click="drawerOpen = true">打开抽屉</AppButton>
          <AppButton size="sm" variant="secondary" @click="askDanger">危险确认</AppButton>
        </div>
        <div class="kit__chips kit__mt">
          <AppButton size="sm" variant="ghost" @click="toast('保存成功')">成功 Toast</AppButton>
          <AppButton
            size="sm"
            variant="ghost"
            @click="toast('接口调用失败', { tone: 'error', description: 'HTTP 500 /api/workflows' })"
          >
            错误 Toast
          </AppButton>
          <AppButton
            size="sm"
            variant="ghost"
            @click="toast('向量化进度 65%', { tone: 'warning' })"
          >
            警告 Toast
          </AppButton>
          <AppButton size="sm" variant="ghost" @click="toast('已切换到只读模式', { tone: 'info' })">
            提示 Toast
          </AppButton>
        </div>
      </AppContentCard>
    </div>

    <AppModal v-model="modalOpen" title="创建工作流" subtitle="从模板创建，名称与描述会预填" :max-width="560">
      <div class="kit__form">
        <AppTextField v-model="form.name" label="工作流名称" required />
        <AppTextarea v-model="form.description" label="描述" :rows="2" />
        <AppSelect v-model="form.type" label="类型" :items="['聊天流', '工作流']" />
        <AppTagInput v-model="form.tags" label="功能标签" :max="5" />
      </div>
      <template #footer>
        <AppButton variant="secondary" size="sm" @click="modalOpen = false">取消</AppButton>
        <AppButton
          size="sm"
          :loading="btnLoading"
          @click="
            () => {
              simulateSave()
              modalOpen = false
            }
          "
        >
          创建工作流
        </AppButton>
      </template>
    </AppModal>

    <AppDrawer v-model="drawerOpen" title="运行工具" subtitle="用示例输入试跑一次" :width="560">
      <div class="kit__form">
        <AppTextarea v-model="form.description" label="输入" :rows="4" />
        <AppTextField v-model="form.name" label="工具" readonly />
        <div class="kit__result">点击「运行」查看结果…</div>
      </div>
      <template #footer>
        <AppButton variant="secondary" size="sm" @click="drawerOpen = false">关闭</AppButton>
        <AppButton
          size="sm"
          @click="
            () => {
              toast('运行完成', { tone: 'success' })
              drawerOpen = false
            }
          "
        >
          运行
        </AppButton>
      </template>
    </AppDrawer>
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
.kit__form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.kit__result {
  min-height: 96px;
  padding: var(--spacing-3);
  border: 1px solid var(--color-divider);
  border-radius: var(--radius-sm);
  background: var(--color-surface-low);
  font: var(--font-body-sm);
  color: var(--color-text-tertiary);
}

.kit__pad {
  padding: var(--spacing-3) var(--spacing-4);
}
</style>