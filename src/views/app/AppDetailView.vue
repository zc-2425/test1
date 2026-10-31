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
  AppTagChip
} from '@/components/ui'
import type { OperationItem } from '@/components/ui'
import { appsApi } from '@/api/resources'
import type { AppDto } from '@/api/types'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'
import { formatDateTime, formatNumber } from '@/utils/format'

/**
 * 应用详情（原型 04-应用中心-智能客服助手.png）。
 * 原型是纯只读两栏：左信息卡 + 右快速操作卡。
 */
const route = useRoute()
const router = useRouter()
const id = String(route.params.id ?? '')

const { data: app, loading, error, notFound, reload } = useResource<AppDto>(() => appsApi.get(id))

const operations: OperationItem[] = [
  { key: 'analytics', label: '查看分析', icon: 'mdi-chart-line', description: '调用量、成功率、成本' },
  { key: 'edit', label: '编辑配置', icon: 'mdi-pencil-outline' },
  { key: 'toggle', label: '启动 / 停止', icon: 'mdi-power' },
  { key: 'delete', label: '删除应用', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onOperation(key: string): Promise<void> {
  if (!app.value) return
  if (key === 'analytics') {
    void router.push('/llmops/overview')
    return
  }
  if (key === 'edit') {
    toast('编辑页在 P7 接入', { tone: 'info' })
    return
  }
  if (key === 'toggle') {
    try {
      const next = app.value.status === '运行中' ? '已停止' : '运行中'
      await appsApi.update(app.value.id, { status: next })
      toast(next === '运行中' ? '已启动' : '已停止', { description: app.value.name })
      await reload()
    } catch (cause) {
      toast('操作失败', { tone: 'error', description: String(cause) })
    }
    return
  }
  const ok = await confirm({
    title: `删除应用「${app.value.name}」`,
    description: '删除后该应用的对外入口会立即失效。',
    confirmText: '删除',
    tone: 'danger'
  })
  if (!ok) return
  try {
    await appsApi.remove(app.value.id)
    toast('已删除', { description: app.value.name })
    void router.push('/app/list')
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
      icon="mdi-application-off-outline"
      title="这个应用不存在"
      description="它可能已被删除，或者链接里的 ID 不对"
    >
      <template #action>
        <AppButton size="sm" icon="mdi-arrow-left" @click="router.push('/app/list')">返回列表</AppButton>
      </template>
    </AppEmptyState>

    <template v-else>
      <AppDetailHeader
        :title="app?.name ?? '加载中…'"
        :subtitle="app?.description"
        :avatar-text="app?.name?.slice(0, 1) ?? '·'"
        back-to="/app/list"
      >
        <template #status>
          <AppStatusBadge v-if="app" :status="app.status" />
          <AppTagChip v-if="app" :label="app.type" class="app-type" />
        </template>
        <template #actions>
          <AppButton variant="secondary" size="sm" icon="mdi-chart-line" @click="onOperation('analytics')">
            查看分析
          </AppButton>
          <AppButton size="sm" icon="mdi-pencil" @click="onOperation('edit')">编辑配置</AppButton>
        </template>
      </AppDetailHeader>

      <div class="u-detail">
        <div class="u-detail__main">
          <AppContentCard title="基本信息">
            <div v-if="loading" class="u-skeleton-stack">
              <span class="u-skeleton" style="width: 55%" />
              <span class="u-skeleton" style="width: 30%" />
            </div>
            <AppKeyValueList
              v-else
              :columns="2"
              :items="[
                { label: '应用类型', value: app?.type },
                { label: '当前状态', value: app?.status },
                { label: '累计使用次数', value: formatNumber(app?.usage_count) },
                { label: '关联 Agent', value: app?.agent_id, variant: 'mono' },
                { label: '关联工作流', value: app?.workflow_id, variant: 'mono' },
                { label: '创建时间', value: formatDateTime(app?.created_at) },
                { label: '更新时间', value: formatDateTime(app?.updated_at) },
                { label: '应用 ID', value: app?.id, variant: 'mono' }
              ]"
            />
          </AppContentCard>

          <AppContentCard title="接入方式" subtitle="把应用嵌进现有系统的三种方式">
            <div class="app-embed">
              <div class="app-embed__item">
                <i class="mdi mdi-code-tags" aria-hidden="true" />
                <div>
                  <p class="app-embed__title">API 调用</p>
                  <p class="app-embed__desc">POST /api/apps/{{ app?.id ?? ':id' }}/chat</p>
                </div>
              </div>
              <div class="app-embed__item">
                <i class="mdi mdi-web" aria-hidden="true" />
                <div>
                  <p class="app-embed__title">网页挂件</p>
                  <p class="app-embed__desc">一段 &lt;script&gt; 嵌入第三方站点</p>
                </div>
              </div>
              <div class="app-embed__item">
                <i class="mdi mdi-forum-outline" aria-hidden="true" />
                <div>
                  <p class="app-embed__title">独立对话页</p>
                  <p class="app-embed__desc">/app/{{ app?.id ?? ':id' }}/chat</p>
                </div>
              </div>
            </div>
          </AppContentCard>
        </div>

        <div class="u-detail__side">
          <AppContentCard title="快速操作" dense>
            <AppOperationCard bare title="" :items="operations" @action="onOperation" />
          </AppContentCard>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.app-type {
  margin-left: var(--spacing-2);
}

.app-embed {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.app-embed__item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border: var(--border-width) solid var(--color-divider);
  border-radius: var(--radius-sm);
}

.app-embed__item .mdi {
  font-size: 18px;
  color: var(--color-primary);
  margin-top: 2px;
}

.app-embed__title {
  font: var(--font-body-md);
  color: var(--color-text);
}

.app-embed__desc {
  font-family: var(--font-family-mono);
  font-size: 12px;
  color: var(--color-text-tertiary);
  word-break: break-all;
}
</style>
