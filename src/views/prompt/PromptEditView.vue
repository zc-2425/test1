<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDetailHeader,
  AppDrawer,
  AppEmptyState,
  AppSelect,
  AppSlider,
  AppTabNav,
  AppTagChip,
  AppTextarea,
  AppTextField
} from '@/components/ui'
import type { TabItem } from '@/components/ui'
import { knowledgeBasesApi, promptsApi } from '@/api/resources'
import {
  getConversation,
  listConversations,
  type ConversationDetail,
  type ConversationDto
} from '@/api/conversations'
import { fetchChatStatus, streamChat, type ChatStatus, type ChatUsage } from '@/api/chat'
import type { KnowledgeBaseDto, PromptDto } from '@/api/types'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'
import { formatDateTime, formatRelative } from '@/utils/format'

/**
 * 提示词编辑器（原型 07-智能聊天助手.png）。
 * 左编辑右测试：左边是提示词正文 + 自动识别出的变量，右边是测试运行面板（流式输出）。
 */
const route = useRoute()
const router = useRouter()
const id = String(route.params.id ?? '')

const { data: prompt, error, notFound } = useResource<PromptDto>(() => promptsApi.get(id))

const activeTab = ref('edit')
const tabs: TabItem[] = [
  { key: 'edit', label: '提示词编辑' },
  { key: 'variables', label: '变量管理' },
  { key: 'model', label: '模型配置' }
]

const content = ref('')
const name = ref('')
const saved = reactive({ content: '', name: '' })
const saving = ref(false)
const testing = ref(false)
const testInput = ref('你们的产品支持私有化部署吗？')
const output = ref('')
const usage = ref<ChatUsage | null>(null)
let controller: AbortController | null = null
const chatStatus = ref<ChatStatus | null>(null)

/* ---------------- 知识库（RAG） ---------------- */
const kbId = ref('')
const { data: kbPage } = useResource(() => knowledgeBasesApi.list({ size: 50 }))
const kbOptions = computed(() => [
  { title: '不使用知识库', value: '' },
  ...((kbPage.value?.items ?? []).map((item: KnowledgeBaseDto) => ({
    title: `${item.name}（${item.doc_count} 个文档）`,
    value: item.id
  })) as { title: string; value: string }[])
])

/* ---------------- 历史会话（P1：真实落库的数据） ---------------- */
const historyOpen = ref(false)
const historyLoading = ref(false)
const historyRows = ref<ConversationDto[]>([])
const historyDetail = ref<ConversationDetail | null>(null)

async function openHistory(): Promise<void> {
  historyOpen.value = true
  await loadHistory()
}

async function loadHistory(): Promise<void> {
  historyLoading.value = true
  historyDetail.value = null
  try {
    const page = await listConversations({ prompt_id: id, size: 20 })
    historyRows.value = page.items
  } catch (cause) {
    toast('历史加载失败', { tone: 'error', description: String(cause) })
  } finally {
    historyLoading.value = false
  }
}

/** 历史消息里的引用是 JSON 文本，这里只取条数 */
function citationCount(raw: string | null | undefined): number {
  if (!raw) return 0
  try {
    const parsed = JSON.parse(raw) as unknown
    return Array.isArray(parsed) ? parsed.length : 0
  } catch {
    return 0
  }
}

async function openHistoryDetail(conversationId: string): Promise<void> {
  try {
    historyDetail.value = await getConversation(conversationId)
  } catch (cause) {
    toast('会话加载失败', { tone: 'error', description: String(cause) })
  }
}

const modelSettings = reactive({
  model: 'gpt-4o',
  temperature: 0.7,
  maxTokens: 2048,
  topP: 1
})

watch(prompt, (value) => {
  if (!value) return
  content.value = value.content
  name.value = value.name
  saved.content = value.content
  saved.name = value.name
  modelSettings.model = value.model_id ?? 'gpt-4o'
})

const dirty = computed(() => content.value !== saved.content || name.value !== saved.name)

// 后端决定走真模型还是模拟，这里只负责如实展示
void fetchChatStatus()
  .then((status) => {
    chatStatus.value = status
  })
  .catch(() => {
    chatStatus.value = null
  })

/** 从正文里抽出 {{变量}}，变量管理 Tab 与左侧 chips 共用 */
const variables = computed(() => {
  const matches = content.value.matchAll(/\{\{\s*([\w.-]+)\s*\}\}/g)
  return [...new Set([...matches].map((m) => m[1]))]
})

const variableNotes = reactive<Record<string, string>>({})

/** 把变量名渲染成双花括号形式（在脚本里拼，避免模板中出现嵌套插值歧义） */
function braced(key: string): string {
  return '{' + '{' + key + '}' + '}'
}
async function save(): Promise<void> {
  if (!prompt.value) return
  saving.value = true
  try {
    await promptsApi.update(prompt.value.id, {
      name: name.value,
      content: content.value,
      model_id: modelSettings.model
    })
    saved.content = content.value
    saved.name = name.value
    toast('已保存', { description: `${name.value} · ${formatDateTime(new Date())}` })
  } catch (cause) {
    toast('保存失败', { tone: 'error', description: String(cause) })
  } finally {
    saving.value = false
  }
}

async function runTest(): Promise<void> {
  if (testing.value) {
    controller?.abort()
    testing.value = false
    return
  }
  controller = new AbortController()
  testing.value = true
  output.value = ''
  usage.value = null
  try {
    usage.value = await streamChat(
      {
        prompt: content.value,
        input: testInput.value,
        promptId: id,
        kbId: kbId.value || undefined,
        model: modelSettings.model,
        temperature: modelSettings.temperature
      },
      (delta) => {
        output.value += delta
      },
      { signal: controller.signal }
    )
    toast('运行完成', { tone: 'success', description: `耗时 ${usage.value.latencyMs} ms` })
  } catch (cause) {
    toast('运行失败', { tone: 'error', description: String(cause) })
  } finally {
    testing.value = false
  }
}

/** 把变量插入光标处（简化：追加到末尾） */
function insertVariable(key: string): void {
  content.value = `${content.value}{{${key}}}`
}
</script>

<template>
  <div class="u-page">
    <p v-if="error" class="u-page__error">{{ error }}</p>

    <AppEmptyState
      v-if="notFound"
      icon="mdi-file-question-outline"
      title="这个提示词不存在"
      description="它可能已被删除，或者链接里的 ID 不对"
    >
      <template #action>
        <AppButton size="sm" icon="mdi-arrow-left" @click="router.push('/prompt/list')">
          返回列表
        </AppButton>
      </template>
    </AppEmptyState>

    <template v-else>
      <AppDetailHeader
        :title="name || '加载中…'"
        :subtitle="
          prompt ? `${prompt.category} · ${prompt.version} · 已使用 ${prompt.usage_count} 次` : ''
        "
        icon="mdi-code-braces"
        back-to="/prompt/list"
      >
        <template #status>
          <AppTagChip v-if="dirty" label="未保存" tone="warning" />
          <AppTagChip v-else-if="prompt" :label="prompt.status" tone="success" />
        </template>
        <template #actions>
          <AppButton variant="secondary" size="sm" icon="mdi-history" @click="openHistory">历史</AppButton>
          <AppButton variant="secondary" size="sm" icon="mdi-play" @click="runTest">
            {{ testing ? '停止' : '运行' }}
          </AppButton>
          <AppButton
            size="sm"
            icon="mdi-content-save"
            :loading="saving"
            :disabled="!dirty"
            @click="save"
          >
            保存
          </AppButton>
        </template>
      </AppDetailHeader>

      <AppTabNav v-model="activeTab" :items="tabs" variant="underline" class="prompt-tabs" />

      <!-- ===== 提示词编辑 ===== -->
      <div v-if="activeTab === 'edit'" class="prompt-edit">
        <div class="prompt-edit__left">
          <AppContentCard title="提示词正文" subtitle="用 {{变量名}} 引用变量，保存后自动提取">
            <div class="prompt-edit__name">
              <AppTextField v-model="name" label="名称" dense />
            </div>
            <textarea
              v-model="content"
              class="prompt-edit__code"
              spellcheck="false"
              placeholder="在这里写提示词…"
            />
            <div class="prompt-edit__vars">
              <span class="prompt-edit__vars-label">检测到的变量</span>
              <AppTagChip
                v-for="key in variables"
                :key="key"
                :label="braced(key)"
                tone="accent"
                clickable
                @click="insertVariable(key)"
              />
              <span v-if="!variables.length" class="prompt-edit__empty">还没有变量</span>
            </div>
          </AppContentCard>
        </div>

        <div class="prompt-edit__right">
          <AppContentCard
            title="测试运行"
            :subtitle="
              chatStatus?.useReal
                ? `真实调用 · ${chatStatus.provider} / ${chatStatus.model}`
                : '模拟输出（未配置模型 Key，写入 server/.env 后自动切换真实调用）'
            "
          >
            <AppSelect
              v-model="kbId"
              label="关联知识库"
              :items="kbOptions"
              class="prompt-edit__kb"
            />
            <AppTextarea v-model="testInput" label="输入" :rows="3" />
            <div class="prompt-edit__run">
              <AppButton size="sm" :icon="testing ? 'mdi-stop' : 'mdi-play'" @click="runTest">
                {{ testing ? '停止' : '运行' }}
              </AppButton>
              <span v-if="usage" class="prompt-edit__usage">
                {{ usage.promptTokens }} → {{ usage.completionTokens }} tokens ·
                {{ usage.latencyMs }} ms
              </span>
              <AppTagChip
                v-if="usage"
                :label="usage.mode === 'real' ? `真实调用 · ${usage.model}` : '模拟输出'"
                :tone="usage.mode === 'real' ? 'success' : 'warning'"
              />
            </div>

            <div class="prompt-edit__output" :class="{ 'is-empty': !output }">
              <template v-if="output">
                <span class="prompt-edit__text">{{ output }}</span>
                <span v-if="testing" class="prompt-edit__cursor" />
              </template>
              <span v-else class="prompt-edit__placeholder">点「运行」查看输出…</span>
            </div>

            <div v-if="usage?.citations.length" class="prompt-edit__citations">
              <p class="prompt-edit__citations-head">
                引用来源 {{ usage.citations.length }} 条 · 检索 {{ usage.ragMs }}ms
              </p>
              <div
                v-for="(cite, index) in usage.citations"
                :key="cite.chunkId"
                class="prompt-edit__citation"
              >
                <span class="prompt-edit__citation-index">[{{ index + 1 }}]</span>
                <span class="prompt-edit__citation-doc">{{ cite.docName }} · 第 {{ cite.position + 1 }} 段</span>
                <span class="prompt-edit__citation-score">{{ cite.score.toFixed(4) }}</span>
                <p class="prompt-edit__citation-preview">{{ cite.preview }}</p>
              </div>
            </div>
          </AppContentCard>
        </div>
      </div>

      <!-- ===== 变量管理 ===== -->
      <AppContentCard
        v-else-if="activeTab === 'variables'"
        title="变量管理"
        subtitle="从正文自动识别；说明只存在本地，用于给自己做备忘"
      >
        <AppEmptyState
          v-if="!variables.length"
          size="sm"
          icon="mdi-code-braces"
          title="还没有变量"
          description="在提示词里写 {{query}} 这样的占位符就会出现在这里"
        />
        <div v-else class="var-list">
          <div v-for="key in variables" :key="key" class="var-list__item">
            <code class="var-list__key">{{ braced(key) }}</code>
            <AppTextField
              :model-value="variableNotes[key] ?? ''"
              label="说明"
              dense
              placeholder="这个变量放什么"
              @update:model-value="(value) => (variableNotes[key] = String(value))"
            />
          </div>
        </div>
      </AppContentCard>

      <!-- ===== 模型配置 ===== -->
      <AppContentCard v-else title="模型配置" subtitle="原型未画这一 Tab，按 LLM 节点的字段补齐">
        <div class="model-grid">
          <AppSelect
            v-model="modelSettings.model"
            label="模型"
            :items="['gpt-4o', 'gpt-4o-mini', 'claude-3-5-sonnet', 'deepseek-chat']"
          />
          <AppTextField
            v-model.number="modelSettings.maxTokens"
            label="最大输出 tokens"
            type="number"
          />
          <AppSlider
            v-model="modelSettings.temperature"
            label="温度"
            :min="0"
            :max="2"
            :step="0.1"
            hint="越高越发散"
          />
          <AppSlider
            v-model="modelSettings.topP"
            label="Top P"
            :min="0"
            :max="1"
            :step="0.05"
            hint="与温度二选一调，不要同时极端"
          />
        </div>
      </AppContentCard>
    </template>

    <AppDrawer
      v-model="historyOpen"
      title="历史会话"
      subtitle="本提示词的真实调用记录（P1 起落库）"
      :width="640"
    >
      <div v-if="!historyDetail" class="history">
        <p v-if="historyLoading" class="history__hint">加载中…</p>
        <p v-else-if="!historyRows.length" class="history__hint">
          还没有调用记录，点右上角「运行」跑一次就会出现在这里。
        </p>
        <button
          v-for="row in historyRows"
          :key="row.id"
          type="button"
          class="history__row"
          @click="openHistoryDetail(row.id)"
        >
          <span class="history__title">{{ row.title || '（无标题会话）' }}</span>
          <span class="history__meta">
            {{ row.message_count }} 条 · {{ row.total_tokens }} tokens ·
            {{ formatRelative(row.updated_at) }}
          </span>
        </button>
      </div>

      <div v-else class="history-detail">
        <AppButton size="sm" variant="ghost" icon="mdi-arrow-left" @click="historyDetail = null">
          返回列表
        </AppButton>
        <div
          v-for="message in historyDetail.messages"
          :key="message.id"
          class="history-msg"
          :class="`is-${message.role}`"
        >
          <div class="history-msg__head">
            <span>{{ message.role === 'user' ? '用户' : '助手' }}</span>
            <span v-if="message.role === 'assistant'" class="history-msg__meta">
              {{ message.tokens }} tokens · {{ message.latency_ms }} ms · {{ message.mode }}
              <span v-if="citationCount(message.citations)">
                · {{ citationCount(message.citations) }} 条引用
              </span>
            </span>
          </div>
          <p class="history-msg__body">{{ message.content }}</p>
        </div>
        <p v-if="historyDetail.traces.length" class="history__trace">
          调用：{{ historyDetail.traces[0].provider }} / {{ historyDetail.traces[0].model }} ·
          {{ historyDetail.traces[0].status }}
        </p>
      </div>

      <template #footer>
        <AppButton size="sm" variant="ghost" icon="mdi-refresh" @click="loadHistory">刷新</AppButton>
        <AppButton size="sm" variant="secondary" @click="historyOpen = false">关闭</AppButton>
      </template>
    </AppDrawer>
  </div>
</template>

<style scoped>
.prompt-tabs {
  margin-bottom: var(--spacing-4);
}

.prompt-edit {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
  gap: var(--spacing-4);
  align-items: start;
}

@media (max-width: 1280px) {
  .prompt-edit {
    grid-template-columns: minmax(0, 1fr);
  }
}

.prompt-edit__left,
.prompt-edit__right {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  min-width: 0;
}

.prompt-edit__name {
  margin-bottom: var(--spacing-3);
}

.prompt-edit__code {
  width: 100%;
  min-height: 360px;
  padding: var(--spacing-3);
  border: var(--border-width) solid var(--color-divider);
  border-radius: var(--radius-sm);
  background: var(--color-surface-low);
  font-family: var(--font-family-mono);
  font-size: 13px;
  line-height: 22px;
  color: var(--color-text);
  resize: vertical;
}

.prompt-edit__code:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: -1px;
}

.prompt-edit__vars {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  margin-top: var(--spacing-3);
}

.prompt-edit__vars-label {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.prompt-edit__empty {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.prompt-edit__run {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  margin-top: var(--spacing-3);
}

.prompt-edit__usage {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  font-variant-numeric: tabular-nums;
}

.prompt-edit__output {
  margin-top: var(--spacing-3);
  min-height: 220px;
  max-height: 420px;
  overflow: auto;
  padding: var(--spacing-3);
  border: var(--border-width) solid var(--color-divider);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font: var(--font-body-md);
  color: var(--color-text);
  line-height: 22px;
  white-space: pre-wrap;
  word-break: break-word;
}

.prompt-edit__output.is-empty {
  background: var(--color-surface-low);
}

.prompt-edit__placeholder {
  color: var(--color-text-tertiary);
}

/* 流式光标 */
.prompt-edit__cursor {
  display: inline-block;
  width: 2px;
  height: 14px;
  margin-left: 2px;
  background: var(--color-primary);
  vertical-align: text-bottom;
  animation: blink 1s steps(2, start) infinite;
}

@keyframes blink {
  to {
    visibility: hidden;
  }
}

.var-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  max-width: 640px;
}

.var-list__item {
  display: grid;
  grid-template-columns: 160px minmax(0, 1fr);
  gap: var(--spacing-3);
  align-items: center;
}

.var-list__key {
  font-family: var(--font-family-mono);
  font-size: 12px;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-container);
  color: var(--color-primary);
  text-align: center;
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-4);
  max-width: 720px;
}
.history {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.history__hint {
  font: var(--font-body-sm);
  color: var(--color-text-tertiary);
  padding: var(--spacing-3) 0;
}

.history__row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--spacing-3);
  border: var(--border-width) solid var(--color-divider);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  text-align: left;
  cursor: pointer;
  font-family: inherit;
}

.history__row:hover {
  border-color: var(--color-primary-light);
}

.history__title {
  font: var(--font-body-md);
  color: var(--color-text);
}

.history__meta {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.history-detail {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.history-msg {
  border-radius: var(--radius-sm);
  padding: var(--spacing-3);
  border: var(--border-width) solid var(--color-divider);
}

.history-msg.is-user {
  background: var(--color-surface-low);
}

.history-msg.is-assistant {
  background: var(--color-surface);
}

.history-msg__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--spacing-2);
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  margin-bottom: 4px;
}

.history-msg__body {
  font: var(--font-body-md);
  color: var(--color-text);
  white-space: pre-wrap;
  line-height: 22px;
}

.history__trace {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}
.prompt-edit__kb {
  margin-bottom: var(--spacing-3);
  max-width: 320px;
}

.prompt-edit__citations {
  margin-top: var(--spacing-3);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.prompt-edit__citations-head {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.prompt-edit__citation {
  border: var(--border-width) solid var(--color-divider);
  border-radius: var(--radius-sm);
  padding: var(--spacing-2) var(--spacing-3);
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 6px var(--spacing-2);
  align-items: baseline;
}

.prompt-edit__citation-index {
  font-family: var(--font-family-mono);
  font-size: 12px;
  color: var(--color-primary);
}

.prompt-edit__citation-doc {
  font: var(--font-label-sm);
  color: var(--color-text-secondary);
}

.prompt-edit__citation-score {
  font-family: var(--font-family-mono);
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.prompt-edit__citation-preview {
  grid-column: 1 / -1;
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  line-height: 18px;
}
</style>
