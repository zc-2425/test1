<script setup lang="ts">
import { useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDataTable,
  AppFilterBar,
  AppPageHeader,
  AppPagination,
  AppRowActions,
  AppSelect,
  AppStatusBadge,
  AppTextField
} from '@/components/ui'
import type { RowAction, TableColumn } from '@/components/ui'
import { agentsApi } from '@/api/resources'
import type { AgentDto } from '@/api/types'
import { useListQuery } from '@/composables/useListQuery'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'
import { formatRelative } from '@/utils/format'

/**
 * AI Agent 列表（原型 06-AI Agent.png）。
 * 「策略」用 soft 徽章与「状态」的 solid 区分，避免两列都是实底造成视觉噪音。
 */
const router = useRouter()

const {
  rows,
  total,
  page,
  size,
  keyword,
  status,
  type: filterType,
  loading,
  error,
  reload,
  onSort,
  resetFilters,
  filtered
} = useListQuery<AgentDto>((query) => agentsApi.list(query))

const columns: TableColumn[] = [
  { key: 'name', title: 'Agent', width: '20%', emphasis: true, ellipsis: true },
  { key: 'type', title: '类型', width: '9%', render: 'tag' },
  { key: 'strategy', title: '推理策略', width: '13%', render: 'badge' },
  { key: 'status', title: '状态', width: '8%', render: 'badge' },
  { key: 'tool_count', title: '工具数', width: '8%', align: 'right', sortable: true },
  { key: 'run_count', title: '运行次数', width: '9%', align: 'right', sortable: true },
  { key: 'last_run_at', title: '最后运行', width: '11%' },
  { key: 'actions', title: '操作', width: '9%', render: 'actions', align: 'right' }
]

const statusOptions = ['活跃', '草稿', '暂停', '错误']
const typeOptions = ['聊天助手', '数据分析', '内容创作', '技术支持', '销售', '办公']

const rowActions: RowAction[] = [
  { key: 'edit', label: '查看详情', icon: 'mdi-eye-outline' },
  { key: 'duplicate', label: '复制', icon: 'mdi-content-copy' },
  { key: 'delete', label: '删除', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onRowAction(key: string, row: AgentDto): Promise<void> {
  if (key === 'run') {
    toast(`已触发运行：${row.name}`, { tone: 'info', description: '运行抽屉在 P6 详情页接入' })
    return
  }
  if (key === 'edit') {
    void router.push(`/agent/${row.id}/detail`)
    return
  }
  if (key === 'duplicate') {
    try {
      await agentsApi.create({
        name: `${row.name} 副本`,
        description: row.description,
        type: row.type,
        strategy: row.strategy,
        system_prompt: row.system_prompt,
        tool_count: row.tool_count
      })
      toast('已复制', { description: `基于「${row.name}」创建` })
      await reload()
    } catch (cause) {
      toast('复制失败', { tone: 'error', description: String(cause) })
    }
    return
  }
  if (key === 'delete') {
    const ok = await confirm({
      title: `删除 Agent「${row.name}」`,
      description: '将同时删除其运行历史与工具授权，操作不可撤销。',
      confirmText: '删除',
      tone: 'danger'
    })
    if (!ok) return
    try {
      await agentsApi.remove(row.id)
      toast('已删除', { description: row.name })
      await reload()
    } catch (cause) {
      toast('删除失败', { tone: 'error', description: String(cause) })
    }
  }
}
</script>

<template>
  <div class="u-page">
    <AppPageHeader title="AI Agent">
      <template #actions>
        <AppButton icon="mdi-plus" @click="router.push('/agent/create')">创建 Agent</AppButton>
      </template>
    </AppPageHeader>

    <AppContentCard flush>
      <AppFilterBar :summary="`共 ${total} 条`">
        <AppTextField
          v-model="keyword"
          dense
          type="search"
          prefix-icon="mdi-magnify"
          placeholder="搜索 Agent 名称…"
        />
        <AppSelect v-model="status" dense :items="statusOptions" placeholder="全部状态" clearable />
        <AppSelect
          v-model="filterType"
          dense
          :items="typeOptions"
          placeholder="全部类型"
          clearable
        />
        <template #actions>
          <AppButton size="sm" variant="ghost" icon="mdi-filter-remove-outline" @click="resetFilters">
            重置
          </AppButton>
          <AppButton size="sm" variant="secondary" icon="mdi-refresh" :loading="loading" @click="reload">
            刷新
          </AppButton>
        </template>
      </AppFilterBar>

      <p v-if="error" class="u-page__error">{{ error }}</p>

      <AppDataTable
        :columns="columns"
        :rows="rows"
        :loading="loading"
        :filtered="filtered"
        clickable-rows
        empty-title="还没有创建 Agent"
        empty-description="从模板开始最快，或者从空白开始自定义"
        @sort="onSort"
        @row-click="(row) => router.push(`/agent/${row.id}/detail`)"
      >
        <template #cell-strategy="{ row }">
          <AppStatusBadge :status="String(row.strategy ?? '')" variant="soft" tone="accent" />
        </template>
        <template #cell-last_run_at="{ row }">
          {{ formatRelative(row.last_run_at as string | null) }}
        </template>
        <template #actions="{ row }">
          <AppRowActions
            :actions="rowActions"
            @action="(key) => onRowAction(key, row as unknown as AgentDto)"
          />
        </template>
        <template #empty-action>
          <AppButton size="sm" icon="mdi-plus" @click="router.push('/agent/create')">
            创建第一个 Agent
          </AppButton>
        </template>
        <template #footer>
          <AppPagination v-model:page="page" v-model:size="size" :total="total" />
        </template>
      </AppDataTable>
    </AppContentCard>
  </div>
</template>
