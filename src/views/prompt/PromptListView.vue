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
import { promptsApi } from '@/api/resources'
import type { PromptDto } from '@/api/types'
import { useListQuery } from '@/composables/useListQuery'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'
import { formatRelative } from '@/utils/format'

/**
 * 提示词管理（原型 07-提示词管理.png）。
 * 分类筛选走 type 参数（后端把 category 映射成了 type_field）。
 */
const router = useRouter()

const {
  rows,
  total,
  page,
  size,
  keyword,
  status,
  type: filterCategory,
  loading,
  error,
  reload,
  onSort,
  resetFilters,
  filtered
} = useListQuery<PromptDto>((query) => promptsApi.list(query), {
  defaultSort: { key: 'updated_at', order: 'desc' }
})

const columns: TableColumn[] = [
  { key: 'name', title: '提示词', width: '22%', emphasis: true, ellipsis: true },
  { key: 'category', title: '分类', width: '9%', render: 'tag' },
  { key: 'version', title: '版本', width: '7%', render: 'mono' },
  { key: 'status', title: '状态', width: '8%', render: 'badge' },
  { key: 'usage_count', title: '使用次数', width: '10%', align: 'right', sortable: true },
  { key: 'updated_at', title: '更新时间', width: '12%', sortable: true },
  { key: 'actions', title: '操作', width: '9%', render: 'actions', align: 'right' }
]

const statusOptions = ['已发布', '草稿']
const categoryOptions = ['通用', '客服', '开发', '内容创作', '办公', '数据分析']

const rowActions: RowAction[] = [
  { key: 'edit', label: '打开编辑器', icon: 'mdi-pencil-outline' },
  { key: 'duplicate', label: '复制一份', icon: 'mdi-content-copy' },
  { key: 'delete', label: '删除', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onRowAction(key: string, row: PromptDto): Promise<void> {
  if (key === 'run' || key === 'edit') {
    void router.push(`/prompt/${row.id}/edit`)
    return
  }
  if (key === 'duplicate') {
    try {
      await promptsApi.create({
        name: `${row.name} 副本`,
        description: row.description,
        category: row.category,
        content: row.content
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
      title: `删除提示词「${row.name}」`,
      description: '引用它的 Agent 与工作流节点会失去该提示词。',
      confirmText: '删除',
      tone: 'danger'
    })
    if (!ok) return
    try {
      await promptsApi.remove(row.id)
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
    <AppPageHeader title="提示词管理">
      <template #actions>
        <AppButton icon="mdi-plus" @click="router.push('/prompt/create')">创建提示词</AppButton>
      </template>
    </AppPageHeader>

    <AppContentCard flush>
      <AppFilterBar :summary="`共 ${total} 条`">
        <AppTextField
          v-model="keyword"
          dense
          type="search"
          prefix-icon="mdi-magnify"
          placeholder="搜索提示词名称…"
        />
        <AppSelect v-model="status" dense :items="statusOptions" placeholder="全部状态" clearable />
        <AppSelect
          v-model="filterCategory"
          dense
          :items="categoryOptions"
          placeholder="全部分类"
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
        empty-title="还没有提示词"
        empty-description="从模板开始，或者从空白提示词开始"
        @sort="onSort"
        @row-click="(row) => router.push(`/prompt/${row.id}/edit`)"
      >
        <template #cell-updated_at="{ row }">
          {{ formatRelative(row.updated_at as string | null) }}
        </template>
        <template #actions="{ row }">
          <AppRowActions
            :actions="rowActions"
            @action="(key) => onRowAction(key, row as unknown as PromptDto)"
          />
        </template>
        <template #empty-action>
          <AppButton size="sm" icon="mdi-plus" @click="router.push('/prompt/create')">
            创建第一个提示词
          </AppButton>
        </template>
        <template #footer>
          <AppPagination v-model:page="page" v-model:size="size" :total="total" />
        </template>
      </AppDataTable>
    </AppContentCard>
  </div>
</template>
