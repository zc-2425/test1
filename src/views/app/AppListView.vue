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
  AppRowActions,
  AppSelect,
  AppTextarea,
  AppTextField,
  AppTagChip
} from '@/components/ui'
import type { RowAction, TableColumn } from '@/components/ui'
import { appsApi } from '@/api/resources'
import type { AppDto } from '@/api/types'
import { useListQuery } from '@/composables/useListQuery'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'

/**
 * 应用管理（原型 04-应用管理.png）。
 * 原型没有创建页，所以「新建」走抽屉——这条路径在 docs/01 里标记为「需补」。
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
} = useListQuery<AppDto>((query) => appsApi.list(query))

const columns: TableColumn[] = [
  { key: 'name', title: '应用', width: '22%', emphasis: true, ellipsis: true },
  { key: 'type', title: '类型', width: '11%', render: 'tag' },
  { key: 'status', title: '状态', width: '9%', render: 'badge' },
  { key: 'usage_count', title: '使用次数', width: '10%', align: 'right', sortable: true },
  { key: 'binding', title: '关联对象', width: '14%', render: 'mono' },
  { key: 'created_at', title: '创建时间', width: '12%', sortable: true },
  { key: 'actions', title: '操作', width: '9%', render: 'actions', align: 'right' }
]

const statusOptions = ['运行中', '已停止', '草稿']
const typeOptions = ['聊天机器人', '智能体', '工作流应用']

const rowActions: RowAction[] = [
  { key: 'detail', label: '查看详情', icon: 'mdi-eye-outline' },
  { key: 'toggle', label: '启动 / 停止', icon: 'mdi-power' },
  { key: 'delete', label: '删除', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onRowAction(key: string, row: AppDto): Promise<void> {
  if (key === 'run' || key === 'detail') {
    void router.push(`/app/${row.id}`)
    return
  }
  if (key === 'toggle') {
    try {
      const next = row.status === '运行中' ? '已停止' : '运行中'
      await appsApi.update(row.id, { status: next })
      toast(next === '运行中' ? '已启动' : '已停止', { description: row.name })
      await reload()
    } catch (cause) {
      toast('操作失败', { tone: 'error', description: String(cause) })
    }
    return
  }
  if (key === 'delete') {
    const ok = await confirm({
      title: `删除应用「${row.name}」`,
      description: '删除后该应用的对外入口会立即失效。',
      confirmText: '删除',
      tone: 'danger'
    })
    if (!ok) return
    try {
      await appsApi.remove(row.id)
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
const draft = reactive({ name: '', type: '聊天机器人', description: '' })

async function submitCreate(): Promise<void> {
  if (!draft.name.trim()) {
    toast('请填写应用名称', { tone: 'warning' })
    return
  }
  submitting.value = true
  try {
    await appsApi.create({ ...draft, status: '草稿' })
    toast('已创建', { description: draft.name })
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
    <AppPageHeader title="应用管理">
      <template #actions>
        <AppButton icon="mdi-plus" @click="drawerOpen = true">创建应用</AppButton>
      </template>
    </AppPageHeader>

    <AppContentCard flush>
      <AppFilterBar :summary="`共 ${total} 条`">
        <AppTextField
          v-model="keyword"
          dense
          type="search"
          prefix-icon="mdi-magnify"
          placeholder="搜索应用名称…"
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
        empty-title="还没有应用"
        empty-description="把 Agent 或工作流包装成对外可用的应用"
        @sort="onSort"
        @row-click="(row) => router.push(`/app/${row.id}`)"
      >
        <template #cell-binding="{ row }">
          {{ row.agent_id || row.workflow_id || '-' }}
        </template>
        <template #cell-created_at="{ row }">
          {{ String(row.created_at ?? '').slice(0, 10) }}
        </template>
        <template #actions="{ row }">
          <AppRowActions
            :actions="rowActions"
            :show-run="false"
            @action="(key) => onRowAction(key, row as unknown as AppDto)"
          />
        </template>
        <template #empty-action>
          <AppButton size="sm" icon="mdi-plus" @click="drawerOpen = true">创建第一个应用</AppButton>
        </template>
        <template #footer>
          <AppPagination v-model:page="page" v-model:size="size" :total="total" />
        </template>
      </AppDataTable>
    </AppContentCard>

    <AppDrawer v-model="drawerOpen" title="创建应用" subtitle="应用 = 对外入口 + 一个 Agent 或工作流">
      <div class="app-form">
        <AppTextField v-model="draft.name" label="应用名称" required placeholder="如：官网客服" />
        <AppSelect v-model="draft.type" label="应用类型" :items="typeOptions" />
        <AppTextarea
          v-model="draft.description"
          label="描述"
          :rows="3"
          hint="一句话说明这个应用解决什么问题"
        />
        <div class="app-form__note">
          <AppTagChip label="草稿态" tone="neutral" />
          <span>创建后状态为草稿，配置好 Agent 再启动</span>
        </div>
      </div>
      <template #footer>
        <AppButton variant="secondary" size="sm" @click="drawerOpen = false">取消</AppButton>
        <AppButton size="sm" :loading="submitting" @click="submitCreate">创建</AppButton>
      </template>
    </AppDrawer>
  </div>
</template>

<style scoped>
.app-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.app-form__note {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}
</style>
