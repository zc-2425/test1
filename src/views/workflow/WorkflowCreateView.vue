<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AppButton,
  AppModal,
  AppPageHeader,
  AppSelect,
  AppTagChip,
  AppTagInput,
  AppTextarea,
  AppTextField
} from '@/components/ui'
import { workflowsApi } from '@/api/resources'
import { toast } from '@/composables/useToast'
import { WORKFLOW_CATEGORIES, WORKFLOW_TEMPLATES, type WorkflowTemplate } from './workflowTemplates'

/**
 * 创建新工作流（原型 03-工作流-创建.png + 03-工作流-模板-弹窗.png）。
 * 分类 chips + 三列模板卡；点「使用此模板」弹出创建弹窗（名称/描述预填），
 * 也可以从 URL 深链打开：/workflow/create?template=doc-qa&modal=1
 */
const route = useRoute()
const router = useRouter()

const activeCategory = ref<string>('全部')
const modalOpen = ref(false)
const submitting = ref(false)
const picked = ref<WorkflowTemplate | null>(null)

const draft = reactive({
  name: '',
  description: '',
  type: '工作流' as '聊天流' | '工作流',
  tags: [] as string[]
})

const visible = computed(() =>
  activeCategory.value === '全部'
    ? WORKFLOW_TEMPLATES
    : WORKFLOW_TEMPLATES.filter((item) => item.category === activeCategory.value)
)

function difficultyTone(difficulty: WorkflowTemplate['difficulty']): 'success' | 'warning' | 'danger' {
  if (difficulty === '简单') return 'success'
  if (difficulty === '中等') return 'warning'
  return 'danger'
}

function openFor(template: WorkflowTemplate): void {
  drafted(template)
  modalOpen.value = true
  void router.replace({ query: { template: template.key, modal: '1' } })
}

function drafted(template: WorkflowTemplate): void {
  picked.value = template
  draft.name = template.name === '空白工作流' ? '未命名工作流' : template.name
  draft.description = template.description
  draft.type = template.type
  draft.tags = [...template.tags]
}

function closeModal(): void {
  modalOpen.value = false
  if (route.query.modal) void router.replace({ query: {} })
}

async function createWorkflow(): Promise<void> {
  if (!picked.value) return
  if (!draft.name.trim()) {
    toast('请填写工作流名称', { tone: 'warning' })
    return
  }
  submitting.value = true
  try {
    const created = await workflowsApi.create({
      name: draft.name,
      description: draft.description,
      type: draft.type,
      node_count: picked.value.nodeCount,
      status: '草稿'
    })
    toast('已创建工作流', { description: `${draft.name} · ${picked.value.nodeCount} 个节点` })
    closeModal()
    void router.push(`/workflow/${created.id}/canvas`)
  } catch (cause) {
    toast('创建失败', { tone: 'error', description: String(cause) })
  } finally {
    submitting.value = false
  }
}

/** 「空白工作流」不进弹窗，直接从 1 个开始节点进画布 */
async function createBlank(): Promise<void> {
  try {
    const created = await workflowsApi.create({
      name: '未命名工作流',
      description: '',
      type: '工作流',
      node_count: 1,
      status: '草稿'
    })
    toast('已创建空白工作流')
    void router.push(`/workflow/${created.id}/canvas`)
  } catch (cause) {
    toast('创建失败', { tone: 'error', description: String(cause) })
  }
}

function onUseTemplate(template: WorkflowTemplate): void {
  if (template.key === 'blank') {
    void createBlank()
    return
  }
  openFor(template)
}

onMounted(() => {
  const templateKey = route.query.template
  if (typeof templateKey !== 'string') return
  const hit = WORKFLOW_TEMPLATES.find((item) => item.key === templateKey)
  if (!hit) return
  drafted(hit)
  modalOpen.value = route.query.modal === '1'
})
</script>

<template>
  <div class="u-page">
    <AppPageHeader
      title="创建新工作流"
      subtitle="选择模板快速开始，或创建空白工作流自定义构建"
      compact
    />

    <div class="wf-create">
      <section class="wf-create__section">
        <h2 class="wf-create__label">选择分类</h2>
        <div class="wf-create__chips">
          <AppTagChip
            v-for="category in WORKFLOW_CATEGORIES"
            :key="category"
            :label="category"
            clickable
            :active="category === activeCategory"
            @click="activeCategory = category"
          />
        </div>
      </section>

      <section class="wf-create__section">
        <h2 class="wf-create__label">工作流模板</h2>
        <div class="wf-grid">
          <article v-for="template in visible" :key="template.key" class="wf-card">
            <header class="wf-card__head">
              <span class="wf-card__icon">
                <i :class="['mdi', template.icon]" aria-hidden="true" />
              </span>
              <div class="wf-card__title">
                <h3 class="wf-card__name">{{ template.name }}</h3>
                <div class="wf-card__badges">
                  <AppTagChip :label="template.type" />
                  <AppTagChip :label="template.difficulty" :tone="difficultyTone(template.difficulty)" />
                </div>
              </div>
            </header>

            <p class="wf-card__desc">{{ template.description }}</p>
            <p class="wf-card__time">预计时间：{{ template.minutes }} 分钟</p>

            <div v-if="template.tags.length" class="wf-card__tags">
              <AppTagChip v-for="tag in template.tags" :key="tag" :label="tag" />
            </div>

            <AppButton size="sm" variant="secondary" icon="mdi-plus" @click="onUseTemplate(template)">
              使用此模板
            </AppButton>
          </article>
        </div>
      </section>
    </div>

    <AppModal
      v-model="modalOpen"
      title="创建工作流"
      subtitle="名称与描述已按模板预填，可以改"
      :max-width="560"
    >
      <div class="wf-modal">
        <AppTextField v-model="draft.name" label="名称" required />
        <AppTextarea v-model="draft.description" label="描述" :rows="2" />
        <AppSelect v-model="draft.type" label="类型" :items="['聊天流', '工作流']" />
        <AppTagInput v-model="draft.tags" label="功能标签" :max="5" />
        <p v-if="picked" class="wf-modal__hint">
          模板 <code>{{ picked.key }}</code> · 初始 {{ picked.nodeCount }} 个节点 · 预计
          {{ picked.minutes }} 分钟
        </p>
      </div>
      <template #footer>
        <AppButton variant="secondary" size="sm" @click="closeModal">取消</AppButton>
        <AppButton size="sm" :loading="submitting" @click="createWorkflow">创建工作流</AppButton>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.wf-create {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-5);
}

.wf-create__section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.wf-create__label {
  font: var(--font-title-md);
  color: var(--color-text);
}

.wf-create__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.wf-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-4);
  padding-bottom: var(--spacing-6);
}

@media (max-width: 1280px) {
  .wf-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.wf-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  background: var(--color-surface);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-md);
}

.wf-card__head {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
}

.wf-card__icon {
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-container);
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.wf-card__title {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.wf-card__name {
  font: var(--font-body-md);
  font-weight: 500;
  color: var(--color-text);
}

.wf-card__badges {
  display: flex;
  gap: var(--spacing-1);
  flex-wrap: wrap;
}

.wf-card__desc {
  font: var(--font-body-sm);
  color: var(--color-text-secondary);
  line-height: 20px;
  min-height: 40px;
}

.wf-card__time {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.wf-card :deep(.app-btn.is-secondary) {
  width: 100%;
}

/* 原型里鼠标悬停的那张卡按钮是紫色实底，默认是描边 */
.wf-card :deep(.app-btn.is-secondary:hover) {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-text-inverse);
}

.wf-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-1);
}

.wf-modal {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.wf-modal__hint {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.wf-modal__hint code {
  font-family: var(--font-family-mono);
  padding: 1px 4px;
  border-radius: var(--radius-xs);
  background: var(--color-surface-low);
}
</style>
