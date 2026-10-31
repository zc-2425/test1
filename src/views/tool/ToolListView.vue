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
import { toolsApi } from '@/api/resources'
import type { ToolDto } from '@/api/types'
import { useListQuery } from '@/composables/useListQuery'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'
import { formatRelative } from '@/utils/format'

/**
 * 工具列表（原型 11-工具.png）。
 * 注意「输入参数」有两套形态：列表展示自然语言版（input_params），
 * 创建页填写的是 schema 版（input_schema）——两者不能混用，否则渲染出不可执行的字符串。
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
} = useListQuery<ToolDto>((query) => toolsApi.list(query), {
  defaultSort: { key: 'updated_at', order: 'desc' }
})

const columns: TableColumn[] = [
  { key: 'name', title: '工具', width: '18%', emphasis: true, ellipsis: true },
  { key: 'type', title: '类型', width: '10%', render: 'tag' },
  { key: 'input_params', title: '输入参数', width: '22%', ellipsis: true },
  { key: 'status', title: '状态', width: '8%', render: 'badge' },
  { key: 'call_count', title: '调用次数', width: '10%', align: 'right', sortable: true },
  { key: 'updated_at', title: '更新时间', width: '12%', sortable: true },
  { key: 'actions', title: '操作', width: '9%', render: 'actions', align: 'right' }
]

const statusOptions = ['可用', '停用']
const typeOptions = ['内置', '自定义API']

const rowActions: RowAction[] = [
  { key: 'detail', label: '查看详情', icon: 'mdi-eye-outline' },
  { key: 'toggle', label: '启用 / 停用', icon: 'mdi-power' },
  { key: 'delete', label: '删除', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onRowAction(key: string, row: ToolDto): Promise<void> {
  if (key === 'run') {
    toast(`已触发运行：${row.name}`, { tone: 'info', description: '运行抽屉在 P6 详情页接入' })
    return
  }
  if (key === 'detail') {
    void router.push(`/tool/${row.id}/detail`)
    return
  }
  if (key === 'toggle') {
    try {
      const next = row.status === '可用' ? '停用' : '可用'
      await toolsApi.update(row.id, { status: next })
      toast(next === '可用' ? '已启用' : '已停用', { description: row.name })
      await reload()
    } catch (cause) {
      toast('操作失败', { tone: 'error', description: String(cause) })
    }
    return
  }
  if (key === 'delete') {
    const ok = await confirm({
      title: `删除工具「${row.name}」`,
      description: '引用它的 Agent 与工作流会失去该工具。',
      confirmText: '删除',
      tone: 'danger'
    })
    if (!ok) return
    try {
      await toolsApi.remove(row.id)
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
    <AppPageHeader title="工具">
      <template #actions>
        <AppButton icon="mdi-plus" @click="router.push('/tool/create')">创建工具</AppButton>
      </template>
    </AppPageHeader>

    <AppContentCard flush>
      <AppFilterBar :summary="`共 ${total} 条`">
        <AppTextField
          v-model="keyword"
          dense
          type="search"
          prefix-icon="mdi-magnify"
          placeholder="搜索工具名称…"
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
        empty-title="还没有工具"
        empty-description="内置工具开箱可用，也可以接入自定义 API"
        @sort="onSort"
        @row-click="(row) => router.push(`/tool/${row.id}/detail`)"
      >
        <template #cell-updated_at="{ row }">
          {{ formatRelative(row.updated_at as string | null) }}
        </template>
        <template #actions="{ row }">
          <AppRowActions
            :actions="rowActions"
            @action="(key) => onRowAction(key, row as unknown as ToolDto)"
          />
        </template>
        <template #empty-action>
          <AppButton size="sm" icon="mdi-plus" @click="router.push('/tool/create')">
            创建第一个工具
          </AppButton>
        </template>
        <template #footer>
          <AppPagination v-model:page="page" v-model:size="size" :total="total" />
        </template>
      </AppDataTable>
    </AppContentCard>
  </div>
</template>
