<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDetailHeader,
  AppEmptyState,
  AppSelect,
  AppSlider,
  AppTabNav,
  AppTagChip,
  AppTextarea,
  AppTextField
} from '@/components/ui'
import type { TabItem } from '@/components/ui'
import { promptsApi } from '@/api/resources'
import { streamChat, type ChatUsage } from '@/api/chat'
import type { PromptDto } from '@/api/types'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'
import { formatDateTime } from '@/utils/format'

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
          <AppContentCard title="测试运行" subtitle="本地模拟流式输出，P12 换成真模型">
            <AppTextarea v-model="testInput" label="输入" :rows="3" />
            <div class="prompt-edit__run">
              <AppButton size="sm" :icon="testing ? 'mdi-stop' : 'mdi-play'" @click="runTest">
                {{ testing ? '停止' : '运行' }}
              </AppButton>
              <span v-if="usage" class="prompt-edit__usage">
                {{ usage.promptTokens }} → {{ usage.completionTokens }} tokens ·
                {{ usage.latencyMs }} ms
              </span>
            </div>
            <div class="prompt-edit__output" :class="{ 'is-empty': !output }">
              <template v-if="output">
                <span class="prompt-edit__text">{{ output }}</span>
                <span v-if="testing" class="prompt-edit__cursor" />
              </template>
              <span v-else class="prompt-edit__placeholder">点「运行」查看输出…</span>
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
</style>
