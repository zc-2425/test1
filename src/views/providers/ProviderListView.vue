<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  AppButton,
  AppContentCard,
  AppEmptyState,
  AppPageHeader,
  AppStatusBadge,
  AppTabNav
} from '@/components/ui'
import type { TabItem } from '@/components/ui'
import { providersApi } from '@/api/resources'
import type { ProviderDto } from '@/api/types'
import { useListQuery } from '@/composables/useListQuery'
import { toast } from '@/composables/useToast'

/**
 * 模型提供商（原型 12-模型提供商.png）。
 * 原型的 4 个 Tab 只有内容区不同，这里用同一个列表 + 客户端过滤实现，
 * 避免为「已配置/未配置」各写一个页面。
 */
const router = useRouter()

const { rows, loading, error, reload } = useListQuery<ProviderDto>((query) =>
  providersApi.list({ ...query, size: 50 })
)

const activeTab = ref('all')

const tabs = computed<TabItem[]>(() => [
  { key: 'all', label: '所有提供商', count: rows.value.length },
  { key: 'enabled', label: '已配置', count: rows.value.filter((p) => p.enabled).length },
  { key: 'disabled', label: '未配置', count: rows.value.filter((p) => !p.enabled).length }
])

const visible = computed(() => {
  if (activeTab.value === 'enabled') return rows.value.filter((item) => item.enabled)
  if (activeTab.value === 'disabled') return rows.value.filter((item) => !item.enabled)
  return rows.value
})

const toggling = ref<string | null>(null)

async function toggleEnabled(provider: ProviderDto, next: boolean): Promise<void> {
  toggling.value = provider.id
  try {
    await providersApi.update(provider.id, { enabled: next })
    toast(next ? '已启用' : '已停用', { description: provider.name })
    await reload()
  } catch (cause) {
    toast('切换失败', { tone: 'error', description: String(cause) })
    await reload()
  } finally {
    toggling.value = null
  }
}
</script>

<template>
  <div class="u-page">
    <AppPageHeader title="模型提供商">
      <template #actions>
        <AppButton icon="mdi-plus" @click="toast('添加提供商在 P7 接入', { tone: 'info' })">
          添加提供商
        </AppButton>
      </template>
    </AppPageHeader>

    <div class="provider-tabs">
      <AppTabNav v-model="activeTab" :items="tabs" variant="pill" />
    </div>

    <p v-if="error" class="u-page__error">{{ error }}</p>

    <div v-if="loading" class="provider-grid">
      <div v-for="i in 6" :key="i" class="provider-card provider-card--skeleton">
        <span class="u-skeleton" style="width: 56%" />
        <span class="u-skeleton" style="width: 34%" />
      </div>
    </div>

    <AppContentCard v-else-if="!visible.length" flush>
      <AppEmptyState
        icon="mdi-atom"
        title="这个分组下没有提供商"
        description="切换到「所有提供商」看看，或者添加一个新的"
      />
    </AppContentCard>

    <div v-else class="provider-grid">
      <div v-for="provider in visible" :key="provider.id" class="provider-card">
        <div class="provider-card__head">
          <span class="provider-card__icon">{{ provider.name.slice(0, 1) }}</span>
          <div class="provider-card__title">
            <span class="provider-card__name">{{ provider.name }}</span>
            <span class="provider-card__meta">{{ provider.model_count }} 个可用模型</span>
          </div>
          <AppStatusBadge :status="provider.status" variant="soft" />
        </div>

        <div class="provider-card__body">
          <span class="provider-card__key">{{ provider.api_key_masked || '未配置密钥' }}</span>
          <span class="provider-card__url">{{ provider.base_url || '默认端点' }}</span>
        </div>

        <div class="provider-card__foot">
          <label class="provider-card__switch">
            <v-switch
              :model-value="provider.enabled"
              :loading="toggling === provider.id"
              color="primary"
              inset
              hide-details
              density="compact"
              @update:model-value="(value) => toggleEnabled(provider, Boolean(value))"
            />
            <span>{{ provider.enabled ? '已启用' : '已停用' }}</span>
          </label>
          <AppButton
            size="sm"
            :variant="provider.enabled ? 'secondary' : 'primary'"
            @click="router.push(`/providers/${provider.id}`)"
          >
            {{ provider.enabled ? '重新配置' : '配置' }}
          </AppButton>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.provider-tabs {
  margin-bottom: var(--spacing-4);
}

.provider-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-4);
}

@media (max-width: 1280px) {
  .provider-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.provider-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  background: var(--color-surface);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-md);
}

.provider-card--skeleton {
  gap: var(--spacing-3);
  min-height: 120px;
}

.provider-card__head {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.provider-card__icon {
  flex: 0 0 auto;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-container);
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
}

.provider-card__title {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.provider-card__name {
  font: var(--font-body-md);
  font-weight: 500;
  color: var(--color-text);
}

.provider-card__meta {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.provider-card__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.provider-card__key {
  font-family: var(--font-family-mono);
  font-size: 12px;
  color: var(--color-text-secondary);
}

.provider-card__url {
  font-family: var(--font-family-mono);
  font-size: 11px;
  color: var(--color-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.provider-card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-2);
  padding-top: var(--spacing-2);
  border-top: var(--border-width) solid var(--color-divider);
}

.provider-card__switch {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  cursor: pointer;
}

.provider-card__switch :deep(.v-switch) {
  flex: 0 0 auto;
}

.provider-card__switch :deep(.v-selection-control) {
  min-height: 28px;
}
</style>
