<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDataTable,
  AppDetailHeader,
  AppDrawer,
  AppEmptyState,
  AppKeyValueList,
  AppOperationCard,
  AppProgressInline,
  AppStatusBadge,
  AppTextField
} from '@/components/ui'
import type { OperationItem, TableColumn } from '@/components/ui'
import { knowledgeBasesApi } from '@/api/resources'
import {
  deleteDocument,
  embeddingStatus,
  listChunks,
  listDocuments,
  reindexKnowledgeBase,
  searchKnowledgeBase,
  uploadDocument,
  type EmbeddingStatus,
  type KbChunkDto,
  type KbDocumentDto,
  type KbSearchResult
} from '@/api/knowledge'
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
const {
  data: documents,
  loading: docsLoading,
  reload: reloadDocs
} = useResource<KbDocumentDto[]>(() => listDocuments(id))

const reindexing = ref(false)

/* ---------------- 上传（真实 multipart） ---------------- */
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)

function pickFile(): void {
  fileInput.value?.click()
}

async function onFileChange(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = '' // 允许连续上传同一个文件
  if (!file || !kb.value) return

  uploading.value = true
  try {
    const result = await uploadDocument(kb.value.id, file)
    toast('上传并索引成功', {
      tone: 'success',
      description: `${result.name} · ${result.chunks} 块 · ${result.mode === 'real' ? '真实向量' : '本地哈希'} · ${result.tookMs}ms`
    })
    await Promise.all([reload(), reloadDocs()])
  } catch (cause) {
    toast('上传失败', {
      tone: 'error',
      description: cause instanceof Error ? cause.message : String(cause)
    })
  } finally {
    uploading.value = false
  }
}

/* ---------------- 分块预览 ---------------- */
const chunksOpen = ref(false)
const chunksLoading = ref(false)
const chunkPage = ref<{ docName: string; total: number; chunks: KbChunkDto[] } | null>(null)

async function openChunks(doc: KbDocumentDto): Promise<void> {
  chunksOpen.value = true
  chunksLoading.value = true
  chunkPage.value = null
  try {
    chunkPage.value = await listChunks(id, doc.id, 50)
  } catch (cause) {
    toast('分块加载失败', { tone: 'error', description: String(cause) })
  } finally {
    chunksLoading.value = false
  }
}

async function removeDoc(doc: KbDocumentDto): Promise<void> {
  const ok = await confirm({
    title: `删除文档「${doc.name}」`,
    description: `将同时删除 ${doc.chunks} 个分块与向量，不可恢复。`,
    confirmText: '删除',
    tone: 'danger'
  })
  if (!ok) return
  try {
    await deleteDocument(id, doc.id)
    toast('已删除', { description: doc.name })
    await Promise.all([reload(), reloadDocs()])
  } catch (cause) {
    toast('删除失败', { tone: 'error', description: String(cause) })
  }
}

/* ---------------- 检索测试（真向量） ---------------- */
const searchQuery = ref('')
const searching = ref(false)
const searchResult = ref<KbSearchResult | null>(null)
const embedMode = ref<EmbeddingStatus | null>(null)

void embeddingStatus()
  .then((status) => {
    embedMode.value = status
  })
  .catch(() => {
    embedMode.value = null
  })

async function runSearch(): Promise<void> {
  if (!searchQuery.value.trim() || searching.value) return
  searching.value = true
  try {
    searchResult.value = await searchKnowledgeBase(id, searchQuery.value.trim(), 5)
  } catch (cause) {
    toast('检索失败', { tone: 'error', description: String(cause) })
  } finally {
    searching.value = false
  }
}

const docColumns: TableColumn[] = [
  { key: 'name', title: '文档', width: '46%', emphasis: true, ellipsis: true },
  { key: 'size', title: '大小', width: '14%', align: 'right' },
  { key: 'chunks', title: '分块数', width: '14%', align: 'right' },
  { key: 'status', title: '状态', width: '14%', render: 'badge' },
  { key: 'actions', title: '操作', width: '18%' }
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
    pickFile()
    return
  }
  if (key === 'recall') {
    searchQuery.value = searchQuery.value || '退款几天到账'
    await runSearch()
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
          <input ref="fileInput" type="file" class="kb-file" @change="onFileChange" />
          <AppButton
            size="sm"
            icon="mdi-cloud-upload-outline"
            :loading="uploading"
            @click="pickFile"
          >
            上传文档
          </AppButton>
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
                { label: '分块大小', value: `${kb?.chunk_size ?? 0} 字符` },
                { label: '分块重叠', value: `${kb?.chunk_overlap ?? 0} 字符` }
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

          <AppContentCard title="文档列表" subtitle="上传后立即切块并向量化，分块可逐条查看" flush>
            <AppDataTable
              :columns="docColumns"
              :rows="(documents ?? []) as unknown as Record<string, unknown>[]"
              :loading="docsLoading"
              dense
              empty-title="还没有文档"
              empty-description="点右上角「上传文档」，支持 txt / md / csv / json（PDF 需装 pypdf）"
            >
              <template #cell-actions="{ row }">
                <div class="kb-row-actions">
                  <AppButton
                    size="sm"
                    variant="ghost"
                    icon="mdi-eye-outline"
                    title="查看分块"
                    @click="openChunks(row as unknown as KbDocumentDto)"
                  />
                  <AppButton
                    size="sm"
                    variant="ghost"
                    icon="mdi-delete-outline"
                    title="删除文档"
                    tone="danger"
                    @click="removeDoc(row as unknown as KbDocumentDto)"
                  />
                </div>
              </template>
            </AppDataTable>
          </AppContentCard>

          <AppContentCard
            title="检索测试"
            :subtitle="
              embedMode
                ? `当前向量：${
                    embedMode.mode === 'real'
                      ? `${embedMode.provider} / ${embedMode.model}（${embedMode.dim} 维）`
                      : '本地哈希向量（离线可用，未配置 Key）'
                  }`
                : '正在读取向量配置…'
            "
          >
            <div class="kb-search">
              <AppTextField
                v-model="searchQuery"
                label="输入一个问题"
                placeholder="例如：退款几天到账"
                @keyup.enter="runSearch"
              />
              <AppButton size="sm" icon="mdi-magnify" :loading="searching" @click="runSearch">
                检索
              </AppButton>
            </div>

            <div v-if="searchResult" class="kb-hits">
              <p class="kb-hits__meta">
                扫描 {{ searchResult.scanned }} 块 · 耗时 {{ searchResult.tookMs }}ms ·
                {{ searchResult.mode === 'real' ? '真向量检索' : '本地哈希检索' }}
              </p>
              <p v-if="!searchResult.hits.length" class="kb-hits__empty">
                没有命中。先上传文档，或者换个更贴近原文的说法。
              </p>
              <div v-for="hit in searchResult.hits" :key="hit.chunkId" class="kb-hit">
                <div class="kb-hit__head">
                  <span class="kb-hit__doc">{{ hit.docName }} · 第 {{ hit.position + 1 }} 段</span>
                  <span class="kb-hit__score">{{ hit.score.toFixed(4) }}</span>
                </div>
                <p class="kb-hit__preview">{{ hit.preview }}</p>
              </div>
            </div>
          </AppContentCard>
        </div>

        <div class="u-detail__side">
          <AppContentCard title="快速操作" dense>
            <AppOperationCard bare title="" :items="operations" @action="onOperation" />
          </AppContentCard>
        </div>
      </div>
    </template>

    <AppDrawer
      v-model="chunksOpen"
      :title="chunkPage?.docName ?? '分块预览'"
      :subtitle="`共 ${chunkPage?.total ?? 0} 块`"
      :width="760"
    >
      <p v-if="chunksLoading" class="kb-hint">加载中…</p>
      <div v-else-if="chunkPage" class="chunk-list">
        <div v-for="chunk in chunkPage.chunks" :key="chunk.id" class="chunk">
          <div class="chunk__head">第 {{ chunk.position + 1 }} 块 · {{ chunk.chars }} 字</div>
          <p class="chunk__body">{{ chunk.content }}</p>
        </div>
      </div>
      <template #footer>
        <AppButton size="sm" variant="secondary" @click="chunksOpen = false">关闭</AppButton>
      </template>
    </AppDrawer>
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
.kb-file {
  display: none;
}

.kb-row-actions {
  display: flex;
  gap: 2px;
}

.kb-search {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-3);
  max-width: 640px;
}

.kb-hits {
  margin-top: var(--spacing-4);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.kb-hits__meta {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.kb-hits__empty {
  font: var(--font-body-sm);
  color: var(--color-text-tertiary);
  padding: var(--spacing-3) 0;
}

.kb-hit {
  border: var(--border-width) solid var(--color-divider);
  border-radius: var(--radius-sm);
  padding: var(--spacing-3);
}

.kb-hit__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--spacing-2);
  margin-bottom: 4px;
}

.kb-hit__doc {
  font: var(--font-label-sm);
  color: var(--color-text-secondary);
}

.kb-hit__score {
  font-family: var(--font-family-mono);
  font-size: 12px;
  color: var(--color-primary);
}

.kb-hit__preview {
  font: var(--font-body-sm);
  color: var(--color-text-secondary);
  line-height: 20px;
  white-space: pre-wrap;
}

.kb-hint {
  font: var(--font-body-sm);
  color: var(--color-text-tertiary);
  padding: var(--spacing-3) 0;
}

.chunk-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.chunk {
  border: var(--border-width) solid var(--color-divider);
  border-radius: var(--radius-sm);
  padding: var(--spacing-3);
}

.chunk__head {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  margin-bottom: 6px;
}

.chunk__body {
  font: var(--font-body-md);
  color: var(--color-text);
  line-height: 22px;
  white-space: pre-wrap;
}
</style>