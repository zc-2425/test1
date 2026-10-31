<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDetailHeader,
  AppFileUploader,
  AppSelect,
  AppTextarea,
  AppTextField
} from '@/components/ui'
import { knowledgeBasesApi } from '@/api/resources'
import { reindexKnowledgeBase } from '@/api/knowledge'
import { toast } from '@/composables/useToast'

/**
 * 创建新知识库（原型 05-知识库-创建.png）。
 * 原型是单列纵向表单、字段拉通整行、左下主按钮。
 * 创建后立刻触发一次重建索引，让「向量化处理中」的进度条真的动起来。
 */
const router = useRouter()

const draft = reactive({
  name: '',
  description: '',
  embeddingModel: 'text-embedding-3-small',
  chunkSize: 800,
  chunkOverlap: 150
})

const files = ref<File[]>([])
const submitting = ref(false)

const embeddingOptions = ['text-embedding-3-small', 'text-embedding-3-large', 'bge-large-zh', 'bge-m3']

async function submit(): Promise<void> {
  if (!draft.name.trim()) {
    toast('请填写知识库名称', { tone: 'warning' })
    return
  }
  const chunkSize = Number(draft.chunkSize)
  const chunkOverlap = Number(draft.chunkOverlap)
  if (Number.isNaN(chunkSize) || chunkSize < 100) {
    toast('分块大小至少 100 tokens', { tone: 'warning' })
    return
  }
  if (Number.isNaN(chunkOverlap) || chunkOverlap >= chunkSize) {
    toast('分块重叠必须小于分块大小', { tone: 'warning' })
    return
  }

  submitting.value = true
  try {
    const created = await knowledgeBasesApi.create({
      name: draft.name,
      description: draft.description,
      embedding_model: draft.embeddingModel,
      chunk_size: chunkSize,
      chunk_overlap: chunkOverlap,
      status: '处理中'
    })
    toast('已创建知识库', { description: `${draft.name} 开始向量化` })
    // 真推一次进度，详情页能看到 5% → 100%
    await reindexKnowledgeBase(created.id)
    void router.push(`/knowledge/${created.id}/detail`)
  } catch (cause) {
    toast('创建失败', { tone: 'error', description: String(cause) })
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="u-page">
    <AppDetailHeader title="创建新知识库" subtitle="上传文档后会自动分块并向量化" back-to="/knowledge/list" />

    <div class="create-form">
      <AppContentCard title="基本信息">
        <div class="create-form__stack">
          <AppTextField
            v-model="draft.name"
            label="知识库名称"
            required
            prefix-icon="mdi-book-open-page-variant-outline"
            placeholder="如：产品文档知识库"
          />
          <AppTextarea
            v-model="draft.description"
            label="描述"
            :rows="2"
            placeholder="这个知识库放什么内容"
          />
          <AppSelect
            v-model="draft.embeddingModel"
            label="嵌入模型"
            :items="embeddingOptions"
            hint="换模型后需要重建索引"
          />
        </div>
      </AppContentCard>

      <AppContentCard title="分段策略" subtitle="分块太大召回不准，太小则上下文断裂">
        <div class="create-form__grid">
          <AppTextField
            v-model.number="draft.chunkSize"
            label="分块大小（tokens）"
            type="number"
            hint="推荐 800"
          />
          <AppTextField
            v-model.number="draft.chunkOverlap"
            label="分块重叠（tokens）"
            type="number"
            hint="推荐为分块大小的 15%~20%"
          />
        </div>
      </AppContentCard>

      <AppContentCard title="文档" subtitle="创建后也可以继续上传；当前版本只保存选择结果">
        <AppFileUploader
          v-model="files"
          accept=".pdf,.docx,.md,.txt,.csv"
          hint="支持 PDF / Word / Markdown / TXT，单文件不超过 50 MB"
          :max-size-mb="50"
          @error="(message) => toast(message, { tone: 'error' })"
        />
      </AppContentCard>

      <div class="create-form__actions">
        <AppButton variant="secondary" @click="router.back()">取消</AppButton>
        <AppButton :loading="submitting" icon="mdi-check" @click="submit">创建知识库</AppButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.create-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  max-width: 820px;
}

.create-form__stack {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.create-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-4);
}

.create-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding-bottom: var(--spacing-6);
}
</style>
