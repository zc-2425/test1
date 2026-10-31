<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppDetailHeader,
  AppEmptyState,
  AppKeyValueList,
  AppOperationCard,
  AppStatusBadge,
  AppTextField
} from '@/components/ui'
import type { OperationItem } from '@/components/ui'
import { providersApi } from '@/api/resources'
import type { ProviderDto } from '@/api/types'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'
import { formatDateTime } from '@/utils/format'

/**
 * 提供商详情（原型 12-模型-AWS Bedrock.png 等 4 份同构数据）。
 * 路由参数既接受 id（prov-001）也接受 slug（aws-bedrock），方便手敲 URL。
 */
const route = useRoute()
const router = useRouter()
const key = String(route.params.id ?? '')

const { data: provider, loading, error, notFound, reload } = useResource<ProviderDto>(async () => {
  try {
    return await providersApi.get(key)
  } catch {
    const page = await providersApi.list({ size: 50 })
    const hit = page.items.find((item) => item.slug === key)
    if (!hit) throw new Error('提供商不存在')
    return hit
  }
})

const editingKey = ref(false)
const keyDraft = ref('')
const testing = ref(false)

const operations: OperationItem[] = [
  { key: 'updateKey', label: '更新 API 密钥', icon: 'mdi-key-outline' },
  { key: 'test', label: '测试连接', icon: 'mdi-lan-connect', description: '发一次轻量请求验证密钥' },
  { key: 'models', label: '查看可用模型', icon: 'mdi-format-list-bulleted' },
  { key: 'delete', label: '删除提供商', icon: 'mdi-trash-can-outline', tone: 'danger' }
]

async function onOperation(action: string): Promise<void> {
  if (!provider.value) return
  if (action === 'updateKey') {
    editingKey.value = true
    keyDraft.value = ''
    return
  }
  if (action === 'models') {
    toast(`${provider.value.model_count} 个模型`, { tone: 'info', description: '模型清单在 P10 接入' })
    return
  }
  if (action === 'test') {
    testing.value = true
    // P12 才会真的打厂商接口；现在按密钥是否存在给出确定性结果
    await new Promise((resolve) => window.setTimeout(resolve, 600))
    testing.value = false
    if (provider.value.api_key_masked) {
      toast('连接成功', { tone: 'success', description: '密钥有效（模拟）' })
    } else {
      toast('连接失败', { tone: 'error', description: '还没有配置 API 密钥' })
    }
    return
  }
  const ok = await confirm({
    title: `删除提供商「${provider.value.name}」`,
    description: '引用它的 Agent 与工作流节点会失去模型来源。',
    confirmText: '删除',
    tone: 'danger'
  })
  if (!ok) return
  try {
    await providersApi.remove(provider.value.id)
    toast('已删除', { description: provider.value.name })
    void router.push('/providers')
  } catch (cause) {
    toast('删除失败', { tone: 'error', description: String(cause) })
  }
}

async function saveKey(): Promise<void> {
  if (!provider.value) return
  if (!keyDraft.value.trim()) {
    toast('密钥不能为空', { tone: 'warning' })
    return
  }
  try {
    // 只存掩码，不落明文（真实项目应在服务端加密存储）
    const masked = `${keyDraft.value.slice(0, 4)}...${keyDraft.value.slice(-4)}`
    await providersApi.update(provider.value.id, { api_key_masked: masked, status: '已连接' })
    editingKey.value = false
    toast('已更新密钥', { description: provider.value.name })
    await reload()
  } catch (cause) {
    toast('更新失败', { tone: 'error', description: String(cause) })
  }
}
</script>

<template>
  <div class="u-page">
    <p v-if="error" class="u-page__error">{{ error }}</p>

    <AppEmptyState
      v-if="notFound"
      icon="mdi-atom-variant"
      title="这个提供商不存在"
      description="检查一下 URL 里的 ID 或 slug"
    >
      <template #action>
        <AppButton size="sm" icon="mdi-arrow-left" @click="router.push('/providers')">
          返回提供商列表
        </AppButton>
      </template>
    </AppEmptyState>

    <template v-else>
      <AppDetailHeader
        :title="provider?.name ?? '加载中…'"
        :subtitle="provider?.base_url ?? provider?.slug"
        :icon="'mdi-atom'"
        back-to="/providers"
      >
        <template #status>
          <AppStatusBadge v-if="provider" :status="provider.status" />
        </template>
        <template #actions>
          <AppButton variant="secondary" size="sm" icon="mdi-lan-connect" :loading="testing" @click="onOperation('test')">
            测试连接
          </AppButton>
          <AppButton size="sm" icon="mdi-key-outline" @click="onOperation('updateKey')">
            更新密钥
          </AppButton>
        </template>
      </AppDetailHeader>

      <div class="u-detail">
        <div class="u-detail__main">
          <AppContentCard title="接入信息">
            <div v-if="loading" class="u-skeleton-stack">
              <span class="u-skeleton" style="width: 60%" />
              <span class="u-skeleton" style="width: 35%" />
            </div>
            <AppKeyValueList
              v-else
              :columns="2"
              :items="[
                { label: 'API 密钥', value: provider?.api_key_masked || '未配置', variant: 'mono' },
                { label: '可用模型', value: `${provider?.model_count ?? 0} 个` },
                { label: '连接状态', value: provider?.status },
                { label: '启用状态', value: provider?.enabled ? '已启用' : '已停用' },
                { label: '接入端点', value: provider?.base_url || '默认端点', variant: 'mono', block: true },
                { label: '标识（slug）', value: provider?.slug, variant: 'mono' },
                { label: '创建时间', value: formatDateTime(provider?.created_at) }
              ]"
            />
          </AppContentCard>

          <AppContentCard v-if="editingKey" title="更新 API 密钥" subtitle="只保存掩码，不落明文">
            <AppTextField
              v-model="keyDraft"
              label="新的 API 密钥"
              type="password"
              prefix-icon="mdi-key-outline"
              placeholder="sk-..."
              hint="留空取消"
            />
            <div class="key-actions">
              <AppButton variant="secondary" size="sm" @click="editingKey = false">取消</AppButton>
              <AppButton size="sm" @click="saveKey">保存</AppButton>
            </div>
          </AppContentCard>

          <AppContentCard title="调用概况" subtitle="数据来自 traces 表，P10 会接真实聚合接口">
            <AppKeyValueList
              :columns="2"
              :items="[
                { label: '近 7 天调用', value: '—' },
                { label: '平均延迟', value: '—' },
                { label: '失败率', value: '—' },
                { label: '预估成本', value: '—' }
              ]"
            />
          </AppContentCard>
        </div>

        <div class="u-detail__side">
          <AppContentCard title="提供商操作" dense>
            <AppOperationCard bare title="" :items="operations" @action="onOperation" />
          </AppContentCard>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.key-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  margin-top: var(--spacing-3);
}
</style>
