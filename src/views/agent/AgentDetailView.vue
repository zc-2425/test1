<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDataTable,
  AppDetailHeader,
  AppEmptyState,
  AppKeyValueList,
  AppOperationCard,
  AppProgressInline,
  AppStatusBadge,
  AppTabNav,
  AppTagChip,
  AppTextarea,
  AppTextField
} from '@/components/ui'
import type { OperationItem, TabItem } from '@/components/ui'
import { agentsApi, toolsApi } from '@/api/resources'
import type { AgentDto, ToolDto } from '@/api/types'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'
import { formatDateTime, formatRelative } from '@/utils/format'

/**
 * Agent 详情（原型 06-智能客服助手.png 等 7 份同构数据）。
 * 三个 Tab：配置（原型有）/ 运行历史（原型未画）/ 工具管理（原型未画）。
 */
const route = useRoute()
const router = useRouter()
const id = String(route.params.id ?? '')

const { data: agent, loading, error, notFound } = useResource<AgentDto>(() => agentsApi.get(id))
const { data: tools } = useResource<ToolDto[]>(() =>
  toolsApi.list({ size: 50 }).then((page) => page.items)
)

const activeTab = ref('config')
const tabs = computed<TabItem[]>(() => [
  { key: 'config', label: '配置' },
  { key: 'history', label: '运行历史' },
  { key: 'tools', label: '工具管理', count: agent.value?.tool_count }
])

const boundTools = computed(() =>
  (tools.value ?? []).filter((tool) => tool.status === '可用').slice(0, agent.value?.tool_count ?? 0)
)

const operations: OperationItem[] = [
  { key: 'run', label: '运行调试', icon: 'mdi-play-circle-outline', description: '用输入试跑一次' },
  { key: 'duplicate', label: '复制 Agent', icon: 'mdi-content-copy' },
  { key: 'export', label: '导出配置', icon: 'mdi-download-outline' },
  { key: 'delete', label: '删除 Agent', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onOperation(key: string): Promise<void> {
  if (!agent.value) return
  if (key === 'run') {
    toast('已触发运行', { tone: 'info', description: '对话调试面板在 P9 接入' })
    return
  }
  if (key === 'duplicate') {
    try {
      await agentsApi.create({
        name: `${agent.value.name} 副本`,
        description: agent.value.description,
        type: agent.value.type,
        strategy: agent.value.strategy,
        system_prompt: agent.value.system_prompt,
        tool_count: agent.value.tool_count
      })
      toast('已复制', { description: '副本已出现在列表里' })
    } catch (cause) {
      toast('复制失败', { tone: 'error', description: String(cause) })
    }
    return
  }
  if (key === 'export') {
    toast('已导出', { description: 'P12 接入真实下载' })
    return
  }
  if (key === 'delete') {
    const ok = await confirm({
      title: `删除 Agent「${agent.value.name}」`,
      description: '将同时删除运行历史与工具授权，不可撤销。',
      confirmText: '删除',
      tone: 'danger'
    })
    if (!ok) return
    try {
      await agentsApi.remove(agent.value.id)
      toast('已删除', { description: agent.value.name })
      void router.push('/agent/list')
    } catch (cause) {
      toast('删除失败', { tone: 'error', description: String(cause) })
    }
  }
}
</script>

<template>
  <div class="u-page">
    <p v-if="error" class="u-page__error">{{ error }}</p>

    <AppEmptyState
      v-if="notFound"
      icon="mdi-robot-confused-outline"
      title="这个 Agent 不存在"
      description="它可能已被删除，或者链接里的 ID 不对"
    >
      <template #action>
        <AppButton size="sm" icon="mdi-arrow-left" @click="router.push('/agent/list')">
          返回列表
        </AppButton>
      </template>
    </AppEmptyState>

    <template v-else>
      <AppDetailHeader
        :title="agent?.name ?? '加载中…'"
        :subtitle="agent?.description"
        :avatar-text="agent?.name?.slice(0, 1) ?? '·'"
        back-to="/agent/list"
      >
        <template #status>
          <AppStatusBadge v-if="agent" :status="agent.status" />
        </template>
        <template #actions>
          <AppButton variant="secondary" size="sm" icon="mdi-play">运行</AppButton>
          <AppButton variant="secondary" size="sm" icon="mdi-content-copy">复制</AppButton>
          <AppButton variant="secondary" size="sm" icon="mdi-share-variant">分享</AppButton>
          <AppButton size="sm" icon="mdi-pencil">编辑</AppButton>
        </template>
      </AppDetailHeader>

      <AppTabNav v-model="activeTab" :items="tabs" variant="underline" class="agent-tabs" />

      <!-- ===== 配置 ===== -->
      <div v-if="activeTab === 'config'" class="u-detail">
        <div class="u-detail__main">
          <AppContentCard title="基本信息">
            <div class="u-detail__fields">
              <AppTextField
                :model-value="agent?.name ?? ''"
                label="Agent 名称"
                readonly
                prefix-icon="mdi-robot-outline"
              />
              <AppTextField
                :model-value="agent?.type ?? ''"
                label="Agent 类型"
                readonly
                prefix-icon="mdi-shape-outline"
              />
            </div>
            <div class="agent-field">
              <AppTextarea :model-value="agent?.description ?? ''" label="描述" :rows="2" readonly />
            </div>
            <div class="u-detail__fields agent-field">
              <AppTextField
                :model-value="agent?.strategy ?? ''"
                label="推理策略"
                readonly
                prefix-icon="mdi-sitemap-outline"
              />
              <AppTextField
                :model-value="agent?.model_id ?? '跟随默认模型'"
                label="模型"
                readonly
                prefix-icon="mdi-brain"
              />
            </div>
          </AppContentCard>

          <AppContentCard title="系统提示词" subtitle="Agent 每次对话都会注入这段指令">
            <AppTextarea
              :model-value="agent?.system_prompt ?? ''"
              :rows="6"
              readonly
              hint="编辑态在 P7 的创建 / 编辑页接入"
            />
          </AppContentCard>
        </div>

        <div class="u-detail__side">
          <AppContentCard title="统计信息" dense>
            <template v-if="agent">
              <AppKeyValueList
                :items="[
                  { label: '创建时间', value: formatDateTime(agent.created_at) },
                  { label: '最后运行', value: formatRelative(agent.last_run_at) },
                  { label: '工具数量', value: agent.tool_count },
                  { label: '运行次数', value: agent.run_count }
                ]"
              />
            </template>
            <div v-else class="u-skeleton-stack">
              <span class="u-skeleton" v-for="i in 4" :key="i" :style="{ width: `${60 + i * 8}%` }" />
            </div>
          </AppContentCard>

          <AppContentCard title="快速操作" dense>
            <AppOperationCard bare title="" :items="operations" @action="onOperation" />
          </AppContentCard>
        </div>
      </div>

      <!-- ===== 运行历史（原型未画） ===== -->
      <AppContentCard v-else-if="activeTab === 'history'" title="运行历史" subtitle="原型没有这一页，按 trace 的字段形态补的">
        <AppDataTable
          :columns="[
            { key: 'id', title: '运行 ID', width: '18%', render: 'mono' },
            { key: 'input', title: '输入', width: '30%', ellipsis: true },
            { key: 'tokens', title: 'Token', width: '12%', align: 'right' },
            { key: 'duration', title: '耗时', width: '12%', align: 'right' },
            { key: 'status', title: '状态', width: '12%', render: 'badge' }
          ]"
          :rows="[]"
          :loading="loading"
          empty-title="还没有运行记录"
          empty-description="点右上角「运行」或列表里的 ▶ 会产生第一条记录"
        >
          <template #empty-action>
            <AppButton size="sm" icon="mdi-play" @click="onOperation('run')">运行一次</AppButton>
          </template>
        </AppDataTable>
      </AppContentCard>

      <!-- ===== 工具管理（原型未画） ===== -->
      <AppContentCard
        v-else
        title="工具管理"
        :subtitle="`已绑定 ${boundTools.length} 个工具（原型未画，按 Agent.tool_count 取可用工具）`"
      >
        <div v-if="boundTools.length" class="agent-tools">
          <div v-for="tool in boundTools" :key="tool.id" class="agent-tools__item">
            <i class="mdi mdi-wrench-outline" aria-hidden="true" />
            <div class="agent-tools__text">
              <span class="agent-tools__name">{{ tool.name }}</span>
              <span class="agent-tools__desc">{{ tool.description }}</span>
            </div>
            <AppTagChip :label="tool.type" />
            <AppProgressInline :value="100" :show-label="false" :width="48" />
            <span class="agent-tools__calls">{{ tool.call_count }} 次</span>
          </div>
        </div>
        <AppEmptyState
          v-else
          size="sm"
          icon="mdi-wrench-outline"
          title="还没有绑定工具"
          description="从工具列表里挑几个，Agent 才能调用外部能力"
        />
        <template #actions>
          <AppButton size="sm" variant="secondary" icon="mdi-plus" @click="router.push('/tool/list')">
            去工具列表
          </AppButton>
        </template>
      </AppContentCard>
    </template>
  </div>
</template>

<style scoped>
.agent-tabs {
  margin-bottom: var(--spacing-4);
}

.agent-field {
  margin-top: var(--spacing-3);
}

.agent-tools {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.agent-tools__item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border: var(--border-width) solid var(--color-divider);
  border-radius: var(--radius-sm);
}

.agent-tools__item .mdi {
  font-size: 18px;
  color: var(--color-primary);
}

.agent-tools__text {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.agent-tools__name {
  font: var(--font-body-md);
  color: var(--color-text);
}

.agent-tools__desc {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-tools__calls {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  white-space: nowrap;
}
</style>
