<script setup lang="ts">
import { useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDataTable,
  AppFilterBar,
  AppPageHeader,
  AppPagination,
  AppProgressInline,
  AppRowActions,
  AppSelect,
  AppTextField
} from '@/components/ui'
import type { RowAction, TableColumn } from '@/components/ui'
import { knowledgeBasesApi } from '@/api/resources'
import { apiPost } from '@/api/http'
import type { KnowledgeBaseDto } from '@/api/types'
import { useListQuery } from '@/composables/useListQuery'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'

/**
 * 知识库管理（原型 05-知识库管理.png）。
 * 注意：知识库（分块 + 向量化）与数据集（解析 + 结构化记录）是两个实体，不可混用。
 */
const router = useRouter()

const {
  rows,
  total,
  page,
  size,
  keyword,
  status,
  loading,
  error,
  reload,
  onSort,
  resetFilters,
  filtered
} = useListQuery<KnowledgeBaseDto>((query) => knowledgeBasesApi.list(query))

const columns: TableColumn[] = [
  { key: 'name', title: '知识库', width: '20%', emphasis: true, ellipsis: true },
  { key: 'doc_count', title: '文档数', width: '8%', align: 'right', sortable: true },
  { key: 'size_label', title: '大小', width: '8%', align: 'right' },
  { key: 'status', title: '向量化状态', width: '11%', render: 'badge' },
  { key: 'vector_progress', title: '进度', width: '14%', render: 'progress' },
  { key: 'embedding_model', title: '嵌入模型', width: '15%', render: 'mono' },
  { key: 'created_at', title: '创建时间', width: '11%', sortable: true },
  { key: 'actions', title: '操作', width: '9%', render: 'actions', align: 'right' }
]

const statusOptions = ['已就绪', '处理中', '失败']

const rowActions: RowAction[] = [
  { key: 'detail', label: '查看详情', icon: 'mdi-eye-outline' },
  { key: 'reindex', label: '重建索引', icon: 'mdi-refresh' },
  { key: 'delete', label: '删除', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onRowAction(key: string, row: KnowledgeBaseDto): Promise<void> {
  if (key === 'run' || key === 'detail') {
    void router.push(`/knowledge/${row.id}/detail`)
    return
  }
  if (key === 'reindex') {
    try {
      // 后端会用后台任务把进度从 5% 推到 100%，列表刷新几次就能看到它动
      await apiPost<KnowledgeBaseDto>(`/knowledge-bases/${row.id}/reindex`)
      toast('已开始重建索引', { description: `${row.name} 的进度会自动推进` })
      await reload()
    } catch (cause) {
      toast('重建失败', { tone: 'error', description: String(cause) })
    }
    return
  }
  if (key === 'delete') {
    const ok = await confirm({
      title: `删除知识库「${row.name}」`,
      description: `将同时删除 ${row.doc_count} 个文档的分块与向量，不可恢复。`,
      confirmText: '删除',
      tone: 'danger'
    })
    if (!ok) return
    try {
      await knowledgeBasesApi.remove(row.id)
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
    <AppPageHeader title="知识库管理">
      <template #actions>
        <AppButton icon="mdi-plus" @click="router.push('/knowledge/create')">创建知识库</AppButton>
      </template>
    </AppPageHeader>

    <AppContentCard flush>
      <AppFilterBar :summary="`共 ${total} 条`">
        <AppTextField
          v-model="keyword"
          dense
          type="search"
          prefix-icon="mdi-magnify"
          placeholder="搜索知识库名称…"
        />
        <AppSelect v-model="status" dense :items="statusOptions" placeholder="全部状态" clearable />
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
        empty-title="还没有知识库"
        empty-description="上传文档后会自动分块并向量化"
        @sort="onSort"
        @row-click="(row) => router.push(`/knowledge/${row.id}/detail`)"
      >
        <template #cell-vector_progress="{ row }">
          <AppProgressInline :value="Number(row.vector_progress ?? 0)" />
        </template>
        <template #cell-created_at="{ row }">
          {{ String(row.created_at ?? '').slice(0, 10) }}
        </template>
        <template #actions="{ row }">
          <AppRowActions
            :actions="rowActions"
            :show-run="false"
            @action="(key) => onRowAction(key, row as unknown as KnowledgeBaseDto)"
          />
        </template>
        <template #empty-action>
          <AppButton size="sm" icon="mdi-plus" @click="router.push('/knowledge/create')">
            创建第一个知识库
          </AppButton>
        </template>
        <template #footer>
          <AppPagination v-model:page="page" v-model:size="size" :total="total" />
        </template>
      </AppDataTable>
    </AppContentCard>
  </div>
</template>
