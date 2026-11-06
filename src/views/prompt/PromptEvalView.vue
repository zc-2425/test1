<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDataTable,
  AppDetailHeader,
  AppModal,
  AppSelect,
  AppStatusBadge,
  AppTagChip,
  AppTextarea,
  AppTextField
} from '@/components/ui'
import type { TableColumn } from '@/components/ui'
import { knowledgeBasesApi, promptsApi } from '@/api/resources'
import {
  createCase,
  deleteCase,
  listCases,
  listRuns,
  runEval,
  updateCase,
  type EvalCaseDto,
  type EvalResultDto,
  type EvalRunDto
} from '@/api/eval'
import type { KnowledgeBaseDto, PromptDto } from '@/api/types'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'
import { formatRelative } from '@/utils/format'

/**
 * 提示词评测（P3）。
 * 判分 = 期望要点命中率，不是让模型自己打分 —— 同一份回答两次必须给出同一个分数，
 * 否则「改好了还是改坏了」就无从判断。
 */
const route = useRoute()
const id = String(route.params.id ?? '')

const { data: prompt } = useResource<PromptDto>(() => promptsApi.get(id))
const { data: cases, reload: reloadCases } = useResource<EvalCaseDto[]>(() => listCases(id))
const { data: runs, reload: reloadRuns } = useResource<EvalRunDto[]>(() => listRuns(id))

const enabledCount = computed(() => (cases.value ?? []).filter((item) => item.enabled).length)

/* ---------------- 新增/编辑用例 ---------------- */
const editorOpen = ref(false)
const editing = ref<EvalCaseDto | null>(null)
const draft = ref({ question: '', expected: '' })
const saving = ref(false)

function openCreate(): void {
  editing.value = null
  draft.value = { question: '', expected: '' }
  editorOpen.value = true
}

function openEdit(item: EvalCaseDto): void {
  editing.value = item
  draft.value = { question: item.question, expected: item.expected }
  editorOpen.value = true
}

async function saveCase(): Promise<void> {
  if (!draft.value.question.trim()) {
    toast('请填写问题', { tone: 'warning' })
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateCase(editing.value.id, {
        question: draft.value.question.trim(),
        expected: draft.value.expected.trim()
      })
      toast('已保存', { tone: 'success' })
    } else {
      await createCase({
        question: draft.value.question.trim(),
        expected: draft.value.expected.trim(),
        prompt_id: id
      })
      toast('已添加用例', { tone: 'success' })
    }
    editorOpen.value = false
    await reloadCases()
  } catch (cause) {
    toast('保存失败', { tone: 'error', description: String(cause) })
  } finally {
    saving.value = false
  }
}

async function toggleCase(item: EvalCaseDto): Promise<void> {
  try {
    await updateCase(item.id, { enabled: !item.enabled })
    await reloadCases()
  } catch (cause) {
    toast('切换失败', { tone: 'error', description: String(cause) })
  }
}

async function removeCase(item: EvalCaseDto): Promise<void> {
  const ok = await confirm({
    title: '删除这条用例',
    description: item.question.slice(0, 60),
    confirmText: '删除',
    tone: 'danger'
  })
  if (!ok) return
  await deleteCase(item.id)
  await reloadCases()
}

/* ---------------- 跑评测 ---------------- */
const threshold = ref(0.6)
/** 评测要挂在知识库上才有意义：不挂就是裸模型在答通用知识 */
const kbId = ref('')
const { data: kbPage } = useResource(() => knowledgeBasesApi.list({ size: 50 }))
const kbOptions = computed<{ title: string; value: string }[]>(() => [
  { title: '不使用知识库', value: '' },
  ...(kbPage.value?.items ?? []).map((item: KnowledgeBaseDto) => ({
    title: `${item.name}（${item.doc_count} 个文档）`,
    value: item.id
  }))
])
const running = ref(false)
const current = ref<{ results: EvalResultDto[]; run: EvalRunDto } | null>(null)
const activeResult = ref<EvalResultDto | null>(null)

async function startRun(): Promise<void> {
  if (!enabledCount.value) {
    toast('至少启用一条用例', { tone: 'warning' })
    return
  }
  running.value = true
  current.value = null
  try {
    const detail = await runEval({
      prompt_id: id,
      kb_id: kbId.value || null,
      threshold: threshold.value,
      note: `阈值 ${threshold.value} · ${kbId.value ? '挂知识库' : '无知识库'}`
    })
    current.value = detail
    await reloadRuns()
    toast('评测完成', {
      tone: detail.run.passed === detail.run.total ? 'success' : 'info',
      description: `${detail.run.passed}/${detail.run.total} 通过 · 平均 ${(detail.run.avg_score * 100).toFixed(0)} 分`
    })
  } catch (cause) {
    toast('评测失败', { tone: 'error', description: String(cause) })
  } finally {
    running.value = false
  }
}

async function openRun(run: EvalRunDto): Promise<void> {
  try {
    const response = await fetch(`/api/eval/runs/${run.id}`)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    current.value = (await response.json()) as { run: EvalRunDto; results: EvalResultDto[] }
  } catch (cause) {
    toast('加载失败', { tone: 'error', description: String(cause) })
  }
}

const resultColumns: TableColumn[] = [
  { key: 'question', title: '用例', width: '38%', emphasis: true, ellipsis: true },
  { key: 'score', title: '得分', width: '12%', align: 'right', render: 'mono' },
  { key: 'matched', title: '命中要点', width: '16%', align: 'right' },
  { key: 'passed', title: '结果', width: '12%' },
  { key: 'latency_ms', title: '耗时', width: '12%', align: 'right', render: 'mono' }
]

const resultRows = computed(() =>
  (current.value?.results ?? []).map((row) => ({
    ...row,
    score: `${(row.score * 100).toFixed(0)}%`,
    matched: `${row.matched}/${row.total_points}`,
    latency_ms: `${row.latency_ms} ms`
  }))
)

const runColumns: TableColumn[] = [
  { key: 'created_at', title: '时间', width: '30%' },
  { key: 'passed', title: '通过', width: '18%', align: 'right' },
  { key: 'avg_score', title: '平均分', width: '18%', align: 'right', render: 'mono' },
  { key: 'took_ms', title: '总耗时', width: '20%', align: 'right', render: 'mono' }
]

const runRows = computed(() =>
  (runs.value ?? []).map((run) => ({
    ...run,
    created_at: formatRelative(run.created_at),
    passed: `${run.passed}/${run.total}`,
    avg_score: `${(run.avg_score * 100).toFixed(0)}%`,
    took_ms: `${(run.took_ms / 1000).toFixed(1)}s`
  }))
)
</script>

<template>
  <div class="u-page">
    <AppDetailHeader
      title="提示词评测"
      :subtitle="prompt ? `${prompt.name} · 判分口径：期望要点命中率` : '判分口径：期望要点命中率'"
      :avatar-text="prompt?.name?.slice(0, 1) ?? '评'"
      :back-to="`/prompt/${id}/edit`"
    >
      <template #status>
        <AppTagChip :label="`${enabledCount} 条启用`" tone="accent" />
      </template>
      <template #actions>
        <AppButton variant="secondary" size="sm" icon="mdi-plus" @click="openCreate">添加用例</AppButton>
        <AppButton size="sm" icon="mdi-play" :loading="running" @click="startRun">运行评测</AppButton>
      </template>
    </AppDetailHeader>

    <div class="eval">
      <div class="eval__main">
        <AppContentCard
          title="用例"
          subtitle="期望要点一行一条；判分时按字面命中率计算，可复现"
          flush
        >
          <div v-if="!cases?.length" class="eval__empty">
            还没有用例。点右上角「添加用例」，把一条真实问题 + 期望答案里的几个关键点写进去。
          </div>
          <div v-else class="cases">
            <div v-for="item in cases" :key="item.id" class="case" :class="{ 'is-off': !item.enabled }">
              <div class="case__head">
                <span class="case__question">{{ item.question }}</span>
                <AppStatusBadge
                  :status="item.enabled ? '启用' : '停用'"
                  :tone="item.enabled ? 'success' : 'neutral'"
                  variant="soft"
                />
                <AppButton size="sm" variant="ghost" icon="mdi-pencil-outline" @click="openEdit(item)" />
                <AppButton
                  size="sm"
                  variant="ghost"
                  :icon="item.enabled ? 'mdi-toggle-switch' : 'mdi-toggle-switch-off-outline'"
                  @click="toggleCase(item)"
                />
                <AppButton size="sm" variant="ghost" tone="danger" icon="mdi-delete-outline" @click="removeCase(item)" />
              </div>
              <p class="case__expected">
                <span class="case__label">期望要点</span>
                {{ item.expected || '（未填写，该用例不会得分）' }}
              </p>
            </div>
          </div>
        </AppContentCard>

        <AppContentCard
          v-if="current"
          :title="`本次结果 · ${current.run.passed}/${current.run.total} 通过`"
          :subtitle="`平均 ${(current.run.avg_score * 100).toFixed(0)} 分 · 阈值 ${current.run.threshold} · ${current.run.mode === 'real' ? '真实调用' : '模拟输出'} · 总耗时 ${(current.run.took_ms / 1000).toFixed(1)}s`"
          flush
        >
          <AppDataTable
            :columns="resultColumns"
            :rows="resultRows"
            dense
            empty-title="没有结果"
            empty-description="换一次运行试试"
          >
            <template #cell-question="{ row }">
              <button type="button" class="eval__link" @click="activeResult = row as unknown as EvalResultDto">
                {{ row.question }}
              </button>
            </template>
            <template #cell-passed="{ row }">
              <AppStatusBadge
                :status="row.passed ? '通过' : '未通过'"
                :tone="row.passed ? 'success' : 'danger'"
                variant="soft"
              />
            </template>
          </AppDataTable>
        </AppContentCard>
      </div>

      <div class="eval__side">
        <AppContentCard title="运行设置" dense>
          <div class="eval__settings">
            <AppSelect v-model="kbId" label="知识库" :items="kbOptions" />
            <AppSelect
              v-model="threshold"
              label="通过阈值"
              :items="[
                { title: '宽松 50%', value: 0.5 },
                { title: '标准 60%', value: 0.6 },
                { title: '严格 80%', value: 0.8 }
              ]"
            />
            <p class="eval__hint">
              评测会用当前保存的提示词内容跑一遍全部启用用例。改完提示词记得先保存，再运行。
            </p>
            <AppButton block size="sm" icon="mdi-play" :loading="running" @click="startRun">
              运行评测
            </AppButton>
          </div>
        </AppContentCard>

        <AppContentCard title="历史运行" subtitle="点一行查看当次明细" flush>
          <AppDataTable
            v-if="runRows.length"
            :columns="runColumns"
            :rows="runRows"
            dense
            clickable-rows
            @row-click="(row: Record<string, unknown>) => openRun(row as unknown as EvalRunDto)"
          />
          <div v-else class="eval__empty">还没有运行记录</div>
        </AppContentCard>
      </div>
    </div>

    <!-- 用例编辑器 -->
    <AppModal v-model="editorOpen" :title="editing ? '编辑用例' : '添加用例'" :max-width="600">
      <div class="editor">
        <AppTextField v-model="draft.question" label="问题" placeholder="例如：退款申请提交后多久到账？" />
        <AppTextarea
          v-model="draft.expected"
          label="期望要点（一行一条）"
          :rows="4"
          placeholder="3 个工作日&#10;原路返回"
        />
        <p class="eval__hint">
          要点写得越贴近「正确答案里一定会出现的措辞」，判分越稳定；同义说法可多写几条。
        </p>
      </div>
      <template #footer>
        <AppButton variant="secondary" size="sm" @click="editorOpen = false">取消</AppButton>
        <AppButton size="sm" :loading="saving" @click="saveCase">保存</AppButton>
      </template>
    </AppModal>

    <!-- 单条结果 -->
    <AppModal
      :model-value="Boolean(activeResult)"
      :title="activeResult?.passed ? '通过' : '未通过'"
      :subtitle="activeResult ? `得分 ${(activeResult.score * 100).toFixed(0)}% · 命中 ${activeResult.matched}/${activeResult.total_points}` : ''"
      :max-width="720"
      @update:model-value="activeResult = null"
    >
      <div v-if="activeResult" class="result-detail">
        <p class="result-detail__label">问题</p>
        <p class="result-detail__text">{{ activeResult.question }}</p>
        <p class="result-detail__label">回答</p>
        <p class="result-detail__text">{{ activeResult.answer }}</p>
        <template v-if="activeResult.missing">
          <p class="result-detail__label">未命中的要点</p>
          <p class="result-detail__text result-detail__missing">{{ activeResult.missing }}</p>
        </template>
      </div>
      <template #footer>
        <AppButton variant="secondary" size="sm" @click="activeResult = null">关闭</AppButton>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.eval {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  gap: var(--spacing-4);
  align-items: start;
}

@media (max-width: 1280px) {
  .eval {
    grid-template-columns: minmax(0, 1fr);
  }
}

.eval__main,
.eval__side {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  min-width: 0;
}

.eval__empty {
  padding: var(--spacing-6) var(--spacing-4);
  text-align: center;
  font: var(--font-body-sm);
  color: var(--color-text-tertiary);
}

.cases {
  display: flex;
  flex-direction: column;
}

.case {
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: var(--border-width) solid var(--color-divider);
}

.case:last-child {
  border-bottom: 0;
}

.case.is-off {
  opacity: 0.55;
}

.case__head {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.case__question {
  flex: 1 1 auto;
  min-width: 0;
  font: var(--font-body-md);
  font-weight: 500;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case__expected {
  margin-top: 4px;
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  white-space: pre-wrap;
}

.case__label {
  color: var(--color-text-secondary);
  margin-right: 6px;
}

.eval__settings {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.eval__hint {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  line-height: 18px;
}

.eval__link {
  border: 0;
  background: transparent;
  padding: 0;
  font: inherit;
  color: var(--color-primary);
  cursor: pointer;
  text-align: left;
}

.editor {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.result-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-detail__label {
  margin-top: var(--spacing-2);
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.result-detail__text {
  font: var(--font-body-sm);
  color: var(--color-text);
  line-height: 21px;
  white-space: pre-wrap;
}

.result-detail__missing {
  color: var(--status-danger);
}
</style>
