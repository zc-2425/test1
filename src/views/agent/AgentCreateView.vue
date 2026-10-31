<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDetailHeader,
  AppSelect,
  AppSlider,
  AppSwitch,
  AppTextarea,
  AppTextField,
  AppTagChip
} from '@/components/ui'
import { agentsApi, knowledgeBasesApi, toolsApi } from '@/api/resources'
import type { KnowledgeBaseDto, ToolDto } from '@/api/types'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'

/**
 * 创建新 Agent（原型 06-Agent-创建.png）。
 * 两栏：主表单 2/3 + 高级配置 1/3；页头带「测试 / 保存」。
 */
const router = useRouter()

const draft = reactive({
  name: '',
  description: '',
  type: '聊天助手',
  strategy: 'Function Calling',
  model: 'gpt-4o',
  systemPrompt: '你是一个智能助手，请根据用户的需求提供帮助。',
  temperature: 0.7,
  maxTurns: 10,
  memory: true,
  toolIds: [] as string[],
  knowledgeId: null as string | null
})

const submitting = ref(false)

const { data: tools } = useResource<ToolDto[]>(() =>
  toolsApi.list({ size: 50 }).then((page) => page.items)
)
const { data: knowledgeBases } = useResource<KnowledgeBaseDto[]>(() =>
  knowledgeBasesApi.list({ size: 50 }).then((page) => page.items)
)

const typeOptions = ['聊天助手', '智能体', '数据分析', '内容创作', '技术支持', '办公']
const strategyOptions = ['Function Calling', 'ReAct', 'Chain of Thought']
const modelOptions = ['gpt-4o', 'gpt-4o-mini', 'claude-3-5-sonnet', 'deepseek-chat']

const toolItems = computed(() =>
  (tools.value ?? []).map((tool) => ({ title: tool.name, value: tool.id }))
)
const kbItems = computed(() =>
  (knowledgeBases.value ?? []).map((kb) => ({ title: kb.name, value: kb.id }))
)

const boundToolNames = computed(() =>
  (tools.value ?? [])
    .filter((tool) => draft.toolIds.includes(tool.id))
    .map((tool) => tool.name)
)

function testRun(): void {
  toast('已发送测试请求', { tone: 'info', description: '流式对话在 P9 接入' })
}

async function submit(): Promise<void> {
  if (!draft.name.trim()) {
    toast('请填写 Agent 名称', { tone: 'warning' })
    return
  }
  submitting.value = true
  try {
    const created = await agentsApi.create({
      name: draft.name,
      description: draft.description,
      type: draft.type,
      strategy: draft.strategy,
      status: '草稿',
      system_prompt: draft.systemPrompt,
      model_id: draft.model,
      tool_count: draft.toolIds.length
    })
    toast('已创建 Agent', { description: `${draft.name}（草稿）` })
    void router.push(`/agent/${created.id}/detail`)
  } catch (cause) {
    toast('创建失败', { tone: 'error', description: String(cause) })
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="u-page">
    <AppDetailHeader
      title="创建新Agent"
      subtitle="配置模型、提示词与可调用的工具"
      back-to="/agent/list"
    >
      <template #actions>
        <AppButton variant="secondary" size="sm" icon="mdi-play" @click="testRun">测试</AppButton>
        <AppButton size="sm" icon="mdi-content-save" :loading="submitting" @click="submit">
          保存
        </AppButton>
      </template>
    </AppDetailHeader>

    <div class="agent-create">
      <div class="agent-create__main">
        <AppContentCard title="基本信息">
          <div class="agent-create__grid">
            <AppTextField
              v-model="draft.name"
              label="Agent 名称"
              required
              prefix-icon="mdi-robot-outline"
              placeholder="如：智能客服助手"
            />
            <AppSelect v-model="draft.type" label="Agent 类型" :items="typeOptions" />
            <AppSelect v-model="draft.strategy" label="推理策略" :items="strategyOptions" />
            <AppSelect v-model="draft.model" label="默认模型" :items="modelOptions" />
          </div>
          <div class="agent-create__stack">
            <AppTextarea
              v-model="draft.description"
              label="描述"
              :rows="2"
              placeholder="一句话说明它能做什么"
            />
          </div>
        </AppContentCard>

        <AppContentCard title="系统提示词" subtitle="每次对话都会注入这段指令">
          <AppTextarea v-model="draft.systemPrompt" label="系统提示词" :rows="6" counter />
        </AppContentCard>

        <AppContentCard title="能力绑定">
          <div class="agent-create__stack">
            <AppSelect
              v-model="draft.toolIds"
              label="可调用的工具"
              :items="toolItems"
              multiple
              hint="多选；Agent 只能调用这里勾选的工具"
            />
            <div v-if="boundToolNames.length" class="agent-create__chips">
              <AppTagChip v-for="name in boundToolNames" :key="name" :label="name" tone="accent" />
            </div>
            <AppSelect
              v-model="draft.knowledgeId"
              label="关联知识库"
              :items="kbItems"
              clearable
              hint="留空表示不使用 RAG"
            />
          </div>
        </AppContentCard>
      </div>

      <div class="agent-create__side">
        <AppContentCard title="高级配置" dense>
          <div class="agent-create__stack">
            <AppSlider
              v-model="draft.temperature"
              label="温度"
              :min="0"
              :max="2"
              :step="0.1"
              hint="越高越发散"
            />
            <AppTextField
              v-model.number="draft.maxTurns"
              label="最大对话轮数"
              type="number"
              hint="超过后自动结束会话"
            />
            <AppSwitch
              v-model="draft.memory"
              label="启用长期记忆"
              description="跨会话记住用户偏好"
              show-state
            />
          </div>
        </AppContentCard>

        <AppContentCard title="创建后" dense>
          <ul class="agent-create__tips">
            <li>状态为草稿，可在详情页点「运行」调试</li>
            <li>工具与知识库绑定可在详情页继续调整</li>
            <li>提示词建议先在编辑器里跑通再发布</li>
          </ul>
        </AppContentCard>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-create {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: var(--spacing-4);
  align-items: start;
}

@media (max-width: 1280px) {
  .agent-create {
    grid-template-columns: minmax(0, 1fr);
  }
}

.agent-create__main,
.agent-create__side {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  min-width: 0;
}

.agent-create__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-4);
}

.agent-create__stack {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  margin-top: var(--spacing-3);
}

.agent-create__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.agent-create__tips {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  font: var(--font-body-sm);
  color: var(--color-text-secondary);
}

.agent-create__tips li {
  padding-left: var(--spacing-4);
  position: relative;
}

.agent-create__tips li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--color-primary);
}
</style>
