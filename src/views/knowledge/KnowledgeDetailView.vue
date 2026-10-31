<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDataTable,
  AppDetailHeader,
  AppEmptyState,
  AppKeyValueList,
  AppOperationCard,
  AppProgressInline,
  AppStatusBadge
} from '@/components/ui'
import type { OperationItem, TableColumn } from '@/components/ui'
import { knowledgeBasesApi } from '@/api/resources'
import { listDocuments, reindexKnowledgeBase, type KbDocumentDto } from '@/api/knowledge'
import type { KnowledgeBaseDto } from '@/api/types'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'
import { formatDateTime } from '@/utils/format'

/**
 * 知识库详情（原型 05-知识库-FAQ知识库.png）。
 * 原型的「向量化处理中 65%」是真的会动：点「重建索引」后端会推进进度。
 */
const route = useRoute()
const router = useRouter()
const id = String(route.params.id ?? '')

const { data: kb, loading, error, notFound, reload } = useResource<KnowledgeBaseDto>(() =>
  knowledgeBasesApi.get(id)
)
const { data: documents, loading: docsLoading } = useResource<KbDocumentDto[]>(() =>
  listDocuments(id)
)

const reindexing = ref(false)

const docColumns: TableColumn[] = [
  { key: 'name', title: '文档', width: '46%', emphasis: true, ellipsis: true },
  { key: 'size', title: '大小', width: '14%', align: 'right' },
  { key: 'chunks', title: '分块数', width: '14%', align: 'right' },
  { key: 'status', title: '状态', width: '16%', render: 'badge' }
]

const operations: OperationItem[] = [
  { key: 'upload', label: '上传文档', icon: 'mdi-cloud-upload-outline', description: '上传后自动分块并向量化' },
  { key: 'reindex', label: '重建索引', icon: 'mdi-refresh' },
  { key: 'recall', label: '召回测试', icon: 'mdi-magnify' },
  { key: 'delete', label: '删除知识库', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onOperation(key: string): Promise<void> {
  if (!kb.value) return
  if (key === 'upload') {
    toast('上传入口在 P7 创建页接入', { tone: 'info' })
    return
  }
  if (key === 'recall') {
    toast('召回测试在 P12 接入', { tone: 'info', description: '需要真实 embedding' })
    return
  }
  if (key === 'reindex') {
    reindexing.value = true
    try {
      await reindexKnowledgeBase(kb.value.id)
      toast('已开始重建索引', { description: '进度会自动推进，刷新可见' })
      // 后端每 2 秒推进一步，轮询几次让进度条真的动起来
      for (let i = 0; i < 6; i += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 2000))
        await reload()
        if ((kb.value?.vector_progress ?? 0) >= 100) break
      }
    } catch (cause) {
      toast('重建失败', { tone: 'error', description: String(cause) })
    } finally {
      reindexing.value = false
    }
    return
  }
  const ok = await confirm({
    title: `删除知识库「${kb.value.name}」`,
    description: `将同时删除 ${kb.value.doc_count} 个文档的分块与向量，不可恢复。`,
    confirmText: '删除',
    tone: 'danger'
  })
  if (!ok) return
  try {
    await knowledgeBasesApi.remove(kb.value.id)
    toast('已删除', { description: kb.value.name })
    void router.push('/knowledge/list')
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
      icon="mdi-book-remove-outline"
      title="这个知识库不存在"
      description="它可能已被删除，或者链接里的 ID 不对"
    >
      <template #action>
        <AppButton size="sm" icon="mdi-arrow-left" @click="router.push('/knowledge/list')">
          返回列表
        </AppButton>
      </template>
    </AppEmptyState>

    <template v-else>
      <AppDetailHeader
        :title="kb?.name ?? '加载中…'"
        :subtitle="kb?.description"
        :avatar-text="kb?.name?.slice(0, 1) ?? '·'"
        back-to="/knowledge/list"
      >
        <template #status>
          <AppStatusBadge v-if="kb" :status="kb.status" />
        </template>
        <template #actions>
          <AppButton
            variant="secondary"
            size="sm"
            icon="mdi-refresh"
            :loading="reindexing"
            @click="onOperation('reindex')"
          >
            重建索引
          </AppButton>
          <AppButton size="sm" icon="mdi-cloud-upload-outline">上传文档</AppButton>
        </template>
      </AppDetailHeader>

      <div class="u-detail">
        <div class="u-detail__main">
          <AppContentCard title="基本信息">
            <div v-if="loading" class="u-skeleton-stack">
              <span class="u-skeleton" style="width: 65%" />
              <span class="u-skeleton" style="width: 40%" />
            </div>
            <AppKeyValueList
              v-else
              :columns="2"
              :items="[
                { label: '文档数量', value: `${kb?.doc_count ?? 0} 个` },
                { label: '占用大小', value: kb?.size_label },
                { label: '嵌入模型', value: kb?.embedding_model, variant: 'mono' },
                { label: '创建时间', value: formatDateTime(kb?.created_at) },
                { label: '分块大小', value: `${kb?.chunk_size ?? 0} tokens` },
                { label: '分块重叠', value: `${kb?.chunk_overlap ?? 0} tokens` }
              ]"
            />
          </AppContentCard>

          <AppContentCard title="向量化进度" :subtitle="kb?.status === '处理中' ? '正在处理，进度会自动推进' : '已完成'">
            <div class="kb-progress">
              <AppProgressInline
                :value="kb?.vector_progress ?? 0"
                :width="520"
                :show-label="false"
                :tone="kb?.status === '失败' ? 'danger' : 'auto'"
              />
              <span class="kb-progress__value">{{ kb?.vector_progress ?? 0 }}%</span>
            </div>
            <p class="kb-progress__hint">
              {{ kb?.doc_count ?? 0 }} 个文档 / {{ kb?.size_label ?? '-' }} / 模型 {{ kb?.embedding_model ?? '-' }}
            </p>
          </AppContentCard>

          <AppContentCard title="文档列表" subtitle="原型没有这一页，按 doc_count 生成的占位文档" flush>
            <AppDataTable
              :columns="docColumns"
              :rows="(documents ?? []) as unknown as Record<string, unknown>[]"
              :loading="docsLoading"
              dense
              empty-title="还没有文档"
              empty-description="上传文档后会自动分块"
            />
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
.kb-progress {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.kb-progress__value {
  font: var(--font-body-md);
  font-weight: 500;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.kb-progress__hint {
  margin-top: var(--spacing-3);
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}
</style>
