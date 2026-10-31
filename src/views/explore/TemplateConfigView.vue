<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDetailHeader,
  AppEmptyState,
  AppFileUploader,
  AppSelect,
  AppSlider,
  AppSwitch,
  AppTagInput,
  AppTextarea,
  AppTextField
} from '@/components/ui'
import { agentsApi, appsApi, datasetsApi, promptsApi, toolsApi, workflowsApi } from '@/api/resources'
import { toast } from '@/composables/useToast'
import { TEMPLATE_SCHEMAS } from './templateSchemas'

/**
 * 配置模板页：一张 schema 驱动 8 张画布
 * （聊天机器人 / 代码助手 / 工作流 / 应用 / 智能体 / 提示词 / 数据集 / 工具模板）。
 *
 * 提交不是假的：按 schema.creates 决定往哪个实体里建，建完跳列表。
 */
const route = useRoute()
const router = useRouter()

const key = computed(() =>
  String(route.params.key ?? (route.meta.templateKey as string | undefined) ?? 'chatbot')
)
const schema = computed(() => TEMPLATE_SCHEMAS[key.value])

/** 表单值用宽松类型，字段的类型安全由 schema + 各控件保证 */
const form = reactive<Record<string, unknown>>({})
const submitting = ref(false)
const files = ref<File[]>([])

function seedForm(): void {
  const current = schema.value
  if (!current) return
  Object.keys(form).forEach((k) => delete form[k])
  for (const section of current.sections) {
    for (const field of section.fields) {
      if (field.control === 'slider') form[field.key] = (field.defaultValue as number) ?? 0.7
      else if (field.control === 'switch') form[field.key] = (field.defaultValue as boolean) ?? false
      else if (field.control === 'tags') form[field.key] = (field.defaultValue as string[]) ?? []
      else if (field.control === 'upload') continue
      else form[field.key] = (field.defaultValue as string) ?? ''
    }
  }
}

watch(schema, seedForm, { immediate: true })

/**
 * 取表单里的字符串值。
 * 注意：空字符串也要走 fallback —— 下拉未选时值是 ''，
 * 如果只在「非字符串」时兜底，会把 '' 一路传到后端，存出一条 type 为空的记录。
 */
function textValue(keyName: string, fallback = ''): string {
  const value = form[keyName]
  if (typeof value !== 'string' || !value.trim()) return fallback
  return value
}

async function submit(): Promise<void> {
  const current = schema.value
  if (!current) return

  const required = current.sections.flatMap((s) => s.fields).filter((f) => f.required)
  const missing = required.find((f) => !textValue(f.key).trim())
  if (missing) {
    toast(`请填写${missing.label}`, { tone: 'warning' })
    return
  }

  submitting.value = true
  try {
    const name = textValue('name')
    const description = textValue('description')

    switch (current.creates) {
      case 'agent':
        await agentsApi.create({
          name,
          description,
          type: textValue('strategy') ? '智能体' : '聊天助手',
          strategy: textValue('strategy', 'Function Calling'),
          system_prompt: textValue('prompt') || textValue('greeting') || textValue('rules'),
          tool_count: (form.tools as string[] | undefined)?.length ?? 0,
          status: '草稿'
        })
        toast('已创建 Agent', { description: name })
        void router.push('/agent/list')
        break
      case 'prompt':
        await promptsApi.create({
          name,
          description,
          category: textValue('category', '通用'),
          content: textValue('template')
        })
        toast('已创建提示词', { description: name })
        void router.push('/prompt/list')
        break
      case 'workflow': {
        const created = await workflowsApi.create({
          name,
          description,
          type: '工作流',
          node_count: 5,
          status: '草稿'
        })
        toast('已创建工作流', { description: name })
        void router.push(`/workflow/${created.id}/canvas`)
        break
      }
      case 'dataset':
        await datasetsApi.create({
          name,
          description,
          type: textValue('type', '文档'),
          parse_status: '待处理'
        })
        toast('已创建数据集', { description: `${name} 待解析` })
        void router.push('/dataset/list')
        break
      case 'app':
        await appsApi.create({
          name,
          description,
          type: textValue('type', '聊天机器人'),
          status: '草稿'
        })
        toast('已创建应用', { description: `${name}（草稿）` })
        void router.push('/app/list')
        break
      case 'tool':
        await toolsApi.create({
          name,
          description,
          type: textValue('type', '内置'),
          input_params: textValue('params'),
          input_schema: textValue('schema')
        })
        toast('已创建工具', { description: name })
        void router.push('/tool/list')
        break
    }
  } catch (cause) {
    toast('创建失败', { tone: 'error', description: String(cause) })
  } finally {
    submitting.value = false
  }
}

</script>

<template>
  <div class="u-page">
    <AppEmptyState
      v-if="!schema"
      icon="mdi-file-question-outline"
      title="这个模板不存在"
      description="检查一下 URL 里的模板 key"
    >
      <template #action>
        <AppButton size="sm" @click="router.push('/explore')">回到模板广场</AppButton>
      </template>
    </AppEmptyState>

    <template v-else>
      <AppDetailHeader :title="schema.title" :icon="schema.icon" back-to="/explore" />

      <div class="tmpl">
        <AppContentCard title="模板说明">
          <p class="tmpl__desc">{{ schema.description }}</p>
        </AppContentCard>

        <AppContentCard v-for="section in schema.sections" :key="section.title" :title="section.title" :subtitle="section.description">
          <div class="tmpl__fields">
            <div
              v-for="field in section.fields"
              :key="field.key"
              :class="{ 'tmpl__field--full': field.block }"
            >
              <AppTextField
                v-if="field.control === 'text'"
                :model-value="textValue(field.key)"
                :label="field.label"
                :required="field.required"
                :placeholder="field.placeholder"
                :hint="field.hint"
                @update:model-value="(value) => (form[field.key] = value)"
              />

              <AppTextarea
                v-else-if="field.control === 'textarea'"
                :model-value="textValue(field.key)"
                :label="field.label"
                :rows="field.rows ?? 3"
                :required="field.required"
                :hint="field.hint"
                @update:model-value="(value) => (form[field.key] = value)"
              />

              <AppSelect
                v-else-if="field.control === 'select'"
                :model-value="textValue(field.key) || null"
                :label="field.label"
                :items="field.options ?? []"
                :required="field.required"
                :hint="field.hint"
                clearable
                @update:model-value="(value) => (form[field.key] = value)"
              />

              <AppSwitch
                v-else-if="field.control === 'switch'"
                :model-value="Boolean(form[field.key])"
                :label="field.label"
                :description="field.hint"
                show-state
                @update:model-value="(value) => (form[field.key] = value)"
              />

              <AppSlider
                v-else-if="field.control === 'slider'"
                :model-value="Number(form[field.key] ?? 0)"
                :label="field.label"
                :min="0"
                :max="1"
                :step="0.1"
                :hint="field.hint"
                @update:model-value="(value) => (form[field.key] = value)"
              />

              <AppTagInput
                v-else-if="field.control === 'tags'"
                :model-value="(form[field.key] as string[]) ?? []"
                :label="field.label"
                :hint="field.hint"
                :max="field.max ?? 5"
                @update:model-value="(value) => (form[field.key] = value)"
              />

              <AppFileUploader
                v-else-if="field.control === 'upload'"
                v-model="files"
                :label="field.label"
                :hint="field.hint"
                @error="(message) => toast(message, { tone: 'error' })"
              />
            </div>
          </div>

          <p v-if="section.fields.some((f) => f.control === 'upload')" class="tmpl__note">
            文件会在创建后由后端解析；当前版本只做到「选中文件」这一步。
          </p>
        </AppContentCard>

        <div class="tmpl__actions">
          <AppButton variant="secondary" @click="router.back()">取消</AppButton>
          <AppButton :loading="submitting" icon="mdi-check" @click="submit">
            创建
          </AppButton>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.tmpl {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  max-width: 760px;
}

.tmpl__desc {
  font: var(--font-body-md);
  color: var(--color-text-secondary);
  line-height: 22px;
}

.tmpl__fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-4);
}

.tmpl__field--full {
  grid-column: 1 / -1;
}

.tmpl__note {
  margin-top: var(--spacing-3);
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.tmpl__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding-bottom: var(--spacing-6);
}
</style>
