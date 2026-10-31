<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDetailHeader,
  AppEmptyState,
  AppKeyValueList,
  AppOperationCard,
  AppProgressInline,
  AppStatusBadge,
  AppTagChip
} from '@/components/ui'
import type { OperationItem } from '@/components/ui'
import { datasetsApi } from '@/api/resources'
import type { DatasetDto } from '@/api/types'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'
import { formatDateTime } from '@/utils/format'

/**
 * 数据集详情（原型 10-数据集-产品知识库.png）。
 * 原型的「创建时间」是空的 —— 这里显式兜底成 -，不渲染空白。
 */
const route = useRoute()
const router = useRouter()
const id = String(route.params.id ?? '')

const { data: dataset, loading, error, notFound } = useResource<DatasetDto>(() =>
  datasetsApi.get(id)
)

const operations: OperationItem[] = [
  { key: 'preview', label: '预览数据', icon: 'mdi-table-eye', description: '查看前 100 条记录' },
  { key: 'export', label: '导出数据', icon: 'mdi-download-outline' },
  { key: 'reparse', label: '重新解析', icon: 'mdi-refresh' },
  { key: 'delete', label: '删除数据集', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onOperation(key: string): Promise<void> {
  if (!dataset.value) return
  if (key === 'preview') {
    toast('预览面板在 P7 接', { tone: 'info' })
    return
  }
  if (key === 'export') {
    toast('导出在 P12 接', { tone: 'info' })
    return
  }
  if (key === 'reparse') {
    try {
      await datasetsApi.update(dataset.value.id, { parse_status: '处理中', progress: 10 })
      toast('已开始重新解析', { description: '进度会随轮询更新' })
    } catch (cause) {
      toast('操作失败', { tone: 'error', description: String(cause) })
    }
    return
  }
  const ok = await confirm({
    title: `删除数据集「${dataset.value.name}」`,
    description: `将同时删除 ${dataset.value.record_count} 条记录，不可恢复。`,
    confirmText: '删除',
    tone: 'danger'
  })
  if (!ok) return
  try {
    await datasetsApi.remove(dataset.value.id)
    toast('已删除', { description: dataset.value.name })
    void router.push('/dataset/list')
  } catch (cause) {
    toast('删除失败', { tone: 'error', description: String(cause) })
  }
}
</script>

<template>
  <div class="u-page">
    <p v-if="error" class="u-page__error">{{ error }}</p>

    <AppEmptyState
      v-if="notFound"
      icon="mdi-database-off-outline"
      title="这个数据集不存在"
      description="它可能已被删除，或者链接里的 ID 不对"
    >
      <template #action>
        <AppButton size="sm" icon="mdi-arrow-left" @click="router.push('/dataset/list')">
          返回列表
        </AppButton>
      </template>
    </AppEmptyState>

    <template v-else>
      <AppDetailHeader
        :title="dataset?.name ?? '加载中…'"
        :subtitle="dataset?.description"
        icon="mdi-database-outline"
        back-to="/dataset/list"
      >
        <template #status>
          <AppStatusBadge v-if="dataset" :status="dataset.parse_status" />
          <AppTagChip v-if="dataset" :label="dataset.type" class="ds-type" />
        </template>
        <template #actions>
          <AppButton variant="secondary" size="sm" icon="mdi-table-eye" @click="onOperation('preview')">
            预览数据
          </AppButton>
          <AppButton size="sm" icon="mdi-download-outline" @click="onOperation('export')">
            导出
          </AppButton>
        </template>
      </AppDetailHeader>

      <div class="u-detail">
        <div class="u-detail__main">
          <AppContentCard title="基本信息">
            <div v-if="loading" class="u-skeleton-stack">
              <span class="u-skeleton" style="width: 60%" />
              <span class="u-skeleton" style="width: 35%" />
            </div>
            <AppKeyValueList
              v-else
              :columns="2"
              :items="[
                { label: '记录数量', value: `${dataset?.record_count ?? 0} 条` },
                { label: '占用大小', value: dataset?.size_label },
                { label: '数据类型', value: dataset?.type },
                { label: '解析状态', value: dataset?.parse_status },
                { label: '创建时间', value: formatDateTime(dataset?.created_at) },
                { label: '更新时间', value: formatDateTime(dataset?.updated_at) }
              ]"
            />
          </AppContentCard>

          <AppContentCard title="解析进度">
            <div class="ds-progress">
              <AppProgressInline
                :value="dataset?.progress ?? 0"
                :width="520"
                :show-label="false"
                :tone="dataset?.parse_status === '失败' ? 'danger' : 'auto'"
              />
              <span class="ds-progress__value">{{ dataset?.progress ?? 0 }}%</span>
            </div>
            <p class="ds-progress__hint">
              {{ dataset?.record_count ?? 0 }} 条记录已解析 / {{ dataset?.size_label ?? '-' }}
            </p>
          </AppContentCard>
        </div>

        <div class="u-detail__side">
          <AppContentCard title="快速操作" dense>
            <AppOperationCard bare title="" :items="operations" @action="onOperation" />
          </AppContentCard>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.ds-type {
  margin-left: var(--spacing-2);
}

.ds-progress {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.ds-progress__value {
  font: var(--font-body-md);
  font-weight: 500;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.ds-progress__hint {
  margin-top: var(--spacing-3);
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}
</style>
