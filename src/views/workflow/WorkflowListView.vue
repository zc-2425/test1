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
  AppTextField
} from '@/components/ui'
import type { RowAction, TableColumn } from '@/components/ui'
import { workflowsApi } from '@/api/resources'
import type { WorkflowDto } from '@/api/types'
import { useListQuery } from '@/composables/useListQuery'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'
import { formatRelative } from '@/utils/format'

/**
 * 工作流管理（原型 03-工作流管理.png）。
 * 列按语义重建：原型的表头与列值错位一位，且多了一个没有数据的「成功率」列位置。
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
} = useListQuery<WorkflowDto>((query) => workflowsApi.list(query))

const columns: TableColumn[] = [
  { key: 'name', title: '工作流', width: '20%', emphasis: true, ellipsis: true },
  { key: 'type', title: '类型', width: '9%', render: 'tag' },
  { key: 'status', title: '状态', width: '9%', render: 'badge' },
  { key: 'node_count', title: '节点数', width: '8%', align: 'right', sortable: true },
  { key: 'last_run_at', title: '最后运行', width: '12%' },
  { key: 'success_rate', title: '成功率', width: '9%', align: 'right', sortable: true },
  { key: 'created_at', title: '创建时间', width: '12%', sortable: true },
  { key: 'actions', title: '操作', width: '9%', render: 'actions', align: 'right' }
]

const statusOptions = ['已发布', '草稿', '运行中']
const typeOptions = ['聊天流', '工作流']

const rowActions: RowAction[] = [
  { key: 'edit', label: '打开画布', icon: 'mdi-pencil-outline' },
  { key: 'duplicate', label: '复制', icon: 'mdi-content-copy' },
  { key: 'delete', label: '删除', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onRowAction(key: string, row: WorkflowDto): Promise<void> {
  if (key === 'run') {
    toast(`已触发运行：${row.name}`, { tone: 'info', description: '节点级 trace 在 P9 画布页接入' })
    return
  }
  if (key === 'edit') {
    void router.push(`/workflow/${row.id}/canvas`)
    return
  }
  if (key === 'duplicate') {
    try {
      await workflowsApi.create({
        name: `${row.name} 副本`,
        description: row.description,
        type: row.type,
        node_count: row.node_count
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
      title: `删除工作流「${row.name}」`,
      description: '删除后无法恢复，引用它的应用会失去该工作流。',
      confirmText: '删除',
      tone: 'danger'
    })
    if (!ok) return
    try {
      await workflowsApi.remove(row.id)
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
    <AppPageHeader title="工作流管理">
      <template #actions>
        <AppButton icon="mdi-plus" @click="router.push('/workflow/create')">创建新工作流</AppButton>
      </template>
    </AppPageHeader>

    <AppContentCard flush>
      <AppFilterBar :summary="`共 ${total} 条`">
        <AppTextField
          v-model="keyword"
          dense
          type="search"
          prefix-icon="mdi-magnify"
          placeholder="搜索工作流名称…"
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
        empty-title="还没有工作流"
        empty-description="从模板创建一个，或者从空白工作流开始"
        @sort="onSort"
        @row-click="(row) => router.push(`/workflow/${row.id}/canvas`)"
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
          <AppRowActions
            :actions="rowActions"
            @action="(key) => onRowAction(key, row as unknown as WorkflowDto)"
          />
        </template>
        <template #empty-action>
          <AppButton size="sm" icon="mdi-plus" @click="router.push('/workflow/create')">
            创建第一个工作流
          </AppButton>
        </template>
        <template #footer>
          <AppPagination v-model:page="page" v-model:size="size" :total="total" />
        </template>
      </AppDataTable>
    </AppContentCard>
  </div>
</template>
