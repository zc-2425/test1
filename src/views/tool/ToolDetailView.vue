<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDetailHeader,
  AppEmptyState,
  AppKeyValueList,
  AppOperationCard,
  AppStatusBadge,
  AppTagChip,
  AppTextarea,
  AppTextField
} from '@/components/ui'
import type { OperationItem } from '@/components/ui'
import { toolsApi } from '@/api/resources'
import type { ToolDto } from '@/api/types'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'
import { formatDateTime } from '@/utils/format'

/**
 * 工具详情（原型 11-工具-文本摘要器.png）。
 * 注意输入参数有两套：input_params 给列表展示的自然语言版，
 * input_schema 给执行用的 schema 版 —— 两者分开渲染。
 */
const route = useRoute()
const router = useRouter()
const id = String(route.params.id ?? '')

const { data: tool, loading, error, notFound } = useResource<ToolDto>(() => toolsApi.get(id))

const operations: OperationItem[] = [
  { key: 'run', label: '运行工具', icon: 'mdi-play-circle-outline', description: '用示例输入试跑' },
  { key: 'edit', label: '编辑配置', icon: 'mdi-pencil-outline' },
  { key: 'stats', label: '查看使用统计', icon: 'mdi-chart-line' },
  { key: 'delete', label: '删除工具', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onOperation(key: string): Promise<void> {
  if (!tool.value) return
  if (key === 'run') {
    toast('已触发运行', { tone: 'info', description: '运行抽屉在 P9 接入' })
    return
  }
  if (key === 'edit') {
    void router.push('/tool/create')
    return
  }
  if (key === 'stats') {
    toast(`已调用 ${tool.value.call_count} 次`, { tone: 'info', description: '统计图表在 P10 的 LLMOps 接入' })
    return
  }
  const ok = await confirm({
    title: `删除工具「${tool.value.name}」`,
    description: '引用它的 Agent 与工作流会失去该工具。',
    confirmText: '删除',
    tone: 'danger'
  })
  if (!ok) return
  try {
    await toolsApi.remove(tool.value.id)
    toast('已删除', { description: tool.value.name })
    void router.push('/tool/list')
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
      icon="mdi-wrench-off-outline"
      title="这个工具不存在"
      description="它可能已被删除，或者链接里的 ID 不对"
    >
      <template #action>
        <AppButton size="sm" icon="mdi-arrow-left" @click="router.push('/tool/list')">返回列表</AppButton>
      </template>
    </AppEmptyState>

    <template v-else>
      <AppDetailHeader
        :title="tool?.name ?? '加载中…'"
        :subtitle="tool?.description"
        icon="mdi-wrench-outline"
        back-to="/tool/list"
      >
        <template #status>
          <AppStatusBadge v-if="tool" :status="tool.status" />
          <AppTagChip v-if="tool" :label="tool.type" class="tool-type" />
        </template>
        <template #actions>
          <AppButton variant="secondary" size="sm" icon="mdi-play" @click="onOperation('run')">运行</AppButton>
          <AppButton size="sm" icon="mdi-pencil" @click="onOperation('edit')">编辑配置</AppButton>
        </template>
      </AppDetailHeader>

      <div class="u-detail">
        <div class="u-detail__main">
          <AppContentCard title="基本信息">
            <div v-if="loading" class="u-skeleton-stack">
              <span class="u-skeleton" style="width: 70%" />
              <span class="u-skeleton" style="width: 45%" />
            </div>
            <div v-else class="u-detail__fields">
              <AppTextField :model-value="tool?.name ?? ''" label="工具名称" readonly prefix-icon="mdi-wrench-outline" />
              <AppTextField :model-value="tool?.type ?? ''" label="工具类型" readonly prefix-icon="mdi-shape-outline" />
            </div>
          </AppContentCard>

          <AppContentCard title="输入参数" subtitle="列表展示用自然语言版；执行用下面这行 schema">
            <AppTextarea
              :model-value="tool?.input_params ?? ''"
              label="参数说明"
              :rows="2"
              readonly
            />
            <div class="tool-schema">
              <span class="tool-schema__label">参数 Schema</span>
              <code class="tool-schema__code">{{ tool?.input_schema || '—' }}</code>
            </div>
          </AppContentCard>
        </div>

        <div class="u-detail__side">
          <AppContentCard title="使用情况" dense>
            <AppKeyValueList
              :items="[
                { label: '调用次数', value: tool?.call_count ?? 0 },
                { label: '创建时间', value: formatDateTime(tool?.created_at) },
                { label: '更新时间', value: formatDateTime(tool?.updated_at) },
                { label: '状态', value: tool?.status }
              ]"
            />
          </AppContentCard>

          <AppContentCard title="快速操作" dense>
            <AppOperationCard bare title="" :items="operations" @action="onOperation" />
          </AppContentCard>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.tool-type {
  margin-left: var(--spacing-2);
}

.tool-schema {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  margin-top: var(--spacing-3);
}

.tool-schema__label {
  font-size: 12px;
  line-height: 16px;
  color: var(--color-text-secondary);
}

.tool-schema__code {
  display: block;
  padding: var(--spacing-2) var(--spacing-3);
  border: var(--border-width) solid var(--color-divider);
  border-radius: var(--radius-sm);
  background: var(--color-surface-low);
  font-family: var(--font-family-mono);
  font-size: 12px;
  color: var(--color-text-secondary);
  word-break: break-all;
}
</style>
