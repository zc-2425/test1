<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDataTable,
  AppDrawer,
  AppFilterBar,
  AppPageHeader,
  AppPagination,
  AppProgressInline,
  AppRowActions,
  AppSelect,
  AppTextarea,
  AppTextField
} from '@/components/ui'
import type { RowAction, TableColumn } from '@/components/ui'
import { datasetsApi } from '@/api/resources'
import type { DatasetDto } from '@/api/types'
import { useListQuery } from '@/composables/useListQuery'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'

/**
 * 数据集管理（原型 10-数据集管理.png）。
 * 原型的「最后更新」列实际渲染的是进度条——这里显式拆成「解析状态 + 进度」两列。
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
} = useListQuery<DatasetDto>((query) => datasetsApi.list(query))

const columns: TableColumn[] = [
  { key: 'name', title: '数据集', width: '20%', emphasis: true, ellipsis: true },
  { key: 'type', title: '类型', width: '9%', render: 'tag' },
  { key: 'record_count', title: '记录数', width: '9%', align: 'right', sortable: true },
  { key: 'size_label', title: '大小', width: '9%', align: 'right' },
  { key: 'parse_status', title: '解析状态', width: '10%', render: 'badge' },
  { key: 'progress', title: '进度', width: '14%', render: 'progress' },
  { key: 'created_at', title: '创建时间', width: '11%' },
  { key: 'actions', title: '操作', width: '9%', render: 'actions', align: 'right' }
]

const statusOptions = ['已完成', '处理中', '待处理', '失败']
const typeOptions = ['文档', '问答对', '表格']

const rowActions: RowAction[] = [
  { key: 'detail', label: '查看详情', icon: 'mdi-eye-outline' },
  { key: 'delete', label: '删除', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onRowAction(key: string, row: DatasetDto): Promise<void> {
  if (key === 'run' || key === 'detail') {
    void router.push(`/dataset/${row.id}/detail`)
    return
  }
  if (key === 'delete') {
    const ok = await confirm({
      title: `删除数据集「${row.name}」`,
      description: `将同时删除 ${row.record_count} 条记录，不可恢复。`,
      confirmText: '删除',
      tone: 'danger'
    })
    if (!ok) return
    try {
      await datasetsApi.remove(row.id)
      toast('已删除', { description: row.name })
      await reload()
    } catch (cause) {
      toast('删除失败', { tone: 'error', description: String(cause) })
    }
  }
}

/* ---------------- 抽屉创建 ---------------- */
const drawerOpen = ref(false)
const submitting = ref(false)
const draft = reactive({ name: '', type: '文档', description: '' })

async function submitCreate(): Promise<void> {
  if (!draft.name.trim()) {
    toast('请填写数据集名称', { tone: 'warning' })
    return
  }
  submitting.value = true
  try {
    await datasetsApi.create({ ...draft, parse_status: '待处理' })
    toast('已创建', { description: `${draft.name} 待解析` })
    drawerOpen.value = false
    draft.name = ''
    draft.description = ''
    await reload()
  } catch (cause) {
    toast('创建失败', { tone: 'error', description: String(cause) })
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="u-page">
    <AppPageHeader title="数据集管理">
      <template #actions>
        <AppButton icon="mdi-plus" @click="drawerOpen = true">创建数据集</AppButton>
      </template>
    </AppPageHeader>

    <AppContentCard flush>
      <AppFilterBar :summary="`共 ${total} 条`">
        <AppTextField
          v-model="keyword"
          dense
          type="search"
          prefix-icon="mdi-magnify"
          placeholder="搜索数据集名称…"
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
        empty-title="还没有数据集"
        empty-description="上传文档或导入问答对，解析后可被 Agent 引用"
        @sort="onSort"
        @row-click="(row) => router.push(`/dataset/${row.id}/detail`)"
      >
        <template #cell-progress="{ row }">
          <AppProgressInline :value="Number(row.progress ?? 0)" />
        </template>
        <template #cell-created_at="{ row }">
          {{ row.created_at ? String(row.created_at).slice(0, 10) : '-' }}
        </template>
        <template #actions="{ row }">
          <AppRowActions
            :actions="rowActions"
            :show-run="false"
            @action="(key) => onRowAction(key, row as unknown as DatasetDto)"
          />
        </template>
        <template #empty-action>
          <AppButton size="sm" icon="mdi-plus" @click="drawerOpen = true">创建第一个数据集</AppButton>
        </template>
        <template #footer>
          <AppPagination v-model:page="page" v-model:size="size" :total="total" />
        </template>
      </AppDataTable>
    </AppContentCard>

    <AppDrawer v-model="drawerOpen" title="创建数据集" subtitle="数据集用于解析结构化记录，与知识库不同">
      <div class="ds-form">
        <AppTextField v-model="draft.name" label="数据集名称" required placeholder="如：产品知识库" />
        <AppSelect v-model="draft.type" label="数据类型" :items="typeOptions" />
        <AppTextarea
          v-model="draft.description"
          label="描述"
          :rows="3"
          hint="说明数据来源与用途"
        />
      </div>
      <template #footer>
        <AppButton variant="secondary" size="sm" @click="drawerOpen = false">取消</AppButton>
        <AppButton size="sm" :loading="submitting" @click="submitCreate">创建</AppButton>
      </template>
    </AppDrawer>
  </div>
</template>

<style scoped>
.ds-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}
</style>
