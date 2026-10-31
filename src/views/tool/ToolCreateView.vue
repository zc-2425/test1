<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDetailHeader,
  AppSelect,
  AppTextarea,
  AppTextField
} from '@/components/ui'
import { toolsApi } from '@/api/resources'
import { toast } from '@/composables/useToast'

/**
 * 创建工具（原型 11-工具-创建工具.png）。
 * 原型这页标题与字段全是英文（Create New Tool / Tool Name ...），按要求中文化。
 * 输入参数拆两套：给列表看的自然语言版 + 给执行用的 schema 版。
 */
const router = useRouter()

const draft = reactive({
  name: '',
  description: '',
  type: '内置',
  inputParams: '',
  inputSchema: ''
})

const submitting = ref(false)
const typeOptions = ['内置', '自定义API']

function validateSchema(value: string): string | null {
  if (!value.trim()) return null
  try {
    JSON.parse(value)
    return null
  } catch {
    return '参数 Schema 必须是合法 JSON'
  }
}

async function submit(): Promise<void> {
  if (!draft.name.trim()) {
    toast('请填写工具名称', { tone: 'warning' })
    return
  }
  const schemaError = validateSchema(draft.inputSchema)
  if (schemaError) {
    toast(schemaError, { tone: 'error' })
    return
  }

  submitting.value = true
  try {
    await toolsApi.create({
      name: draft.name,
      description: draft.description,
      type: draft.type,
      input_params: draft.inputParams,
      input_schema: draft.inputSchema,
      status: '可用'
    })
    toast('已创建工具', { description: draft.name })
    void router.push('/tool/list')
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
      title="创建工具"
      subtitle="把内部能力包装成 Agent 可调用的工具"
      back-to="/tool/list"
    >
      <template #actions>
        <AppButton size="sm" icon="mdi-content-save" :loading="submitting" @click="submit">
          保存
        </AppButton>
      </template>
    </AppDetailHeader>

    <div class="tool-create">
      <AppContentCard title="基本信息">
        <div class="tool-create__stack">
          <AppTextField
            v-model="draft.name"
            label="工具名称"
            required
            prefix-icon="mdi-wrench-outline"
            placeholder="如：订单查询"
          />
          <AppTextField
            v-model="draft.description"
            label="描述"
            prefix-icon="mdi-text-short"
            placeholder="一句话说明它能做什么"
            hint="Agent 会靠这句描述判断什么时候调用它"
          />
          <AppSelect v-model="draft.type" label="工具类型" :items="typeOptions" />
        </div>
      </AppContentCard>

      <AppContentCard title="输入参数" subtitle="两套形态各管一件事，不要混用">
        <div class="tool-create__stack">
          <AppTextField
            v-model="draft.inputParams"
            label="参数说明（列表展示用）"
            placeholder="如：订单号, 是否需要明细"
            hint="用户读的自然语言版"
          />
          <AppTextarea
            v-model="draft.inputSchema"
            label="参数 Schema（执行用）"
            :rows="4"
            placeholder='{"orderId":"string","withDetail":"boolean"}'
            hint="合法 JSON；留空表示无参数"
          />
        </div>
      </AppContentCard>

      <div class="tool-create__actions">
        <AppButton variant="secondary" @click="router.back()">取消</AppButton>
        <AppButton :loading="submitting" icon="mdi-check" @click="submit">创建工具</AppButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tool-create {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  max-width: 760px;
}

.tool-create__stack {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.tool-create__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding-bottom: var(--spacing-6);
}
</style>
