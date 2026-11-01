<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AppButton,
  AppModal,
  AppPageHeader,
  AppSelect,
  AppSlider,
  AppStatusBadge,
  AppSwitch,
  AppTabNav,
  AppTagChip,
  AppTextarea
} from '@/components/ui'
import type { TabItem } from '@/components/ui'
import { getAlerts, resolveAlert, type AlertDto } from '@/api/llmops'
import { toast } from '@/composables/useToast'
import { formatDateTime } from '@/utils/format'

/**
 * LLMOps 布局：标题 + 5 个 Tab + 两个全局弹窗。
 *
 * 弹窗由 query 驱动（?alerts=1 / ?settings=1），这样任何 Tab 上都能打开同一个告警中心，
 * 也方便直接分享链接。
 */
const route = useRoute()
const router = useRouter()

const TABS: TabItem[] = [
  { key: 'llmops-overview', label: '概览' },
  { key: 'llmops-models', label: '模型监控' },
  { key: 'llmops-cost', label: '成本管理' },
  { key: 'llmops-ab-test', label: 'A/B 测试' },
  { key: 'llmops-security', label: '安全合规' }
]

const activeTab = computed({
  get: () => String(route.name ?? 'llmops-overview'),
  set: (key: string) => {
    const name = TABS.find((item) => item.key === key)?.key
    if (name && name !== route.name) void router.push({ name })
  }
})

/* ---------------- 告警中心弹窗 ---------------- */
const alertsOpen = computed({
  get: () => route.query.alerts === '1',
  set: (value: boolean) => {
    void router.replace({ query: value ? { ...route.query, alerts: '1' } : omitQuery('alerts') })
  }
})

const alerts = ref<AlertDto[]>([])
const alertsLoading = ref(false)

async function loadAlerts(): Promise<void> {
  alertsLoading.value = true
  try {
    alerts.value = await getAlerts()
  } catch (cause) {
    toast('告警加载失败', { tone: 'error', description: String(cause) })
  } finally {
    alertsLoading.value = false
  }
}

async function resolve(alert: AlertDto): Promise<void> {
  try {
    await resolveAlert(alert.id)
    toast('已标记为已解决', { description: alert.title })
    await loadAlerts()
  } catch (cause) {
    toast('操作失败', { tone: 'error', description: String(cause) })
  }
}

watch(
  () => route.query.alerts,
  (value) => {
    if (value === '1') void loadAlerts()
  },
  { immediate: true }
)

/* ---------------- LLMOps 设置弹窗 ---------------- */
const settingsOpen = computed({
  get: () => route.query.settings === '1',
  set: (value: boolean) => {
    void router.replace({ query: value ? { ...route.query, settings: '1' } : omitQuery('settings') })
  }
})

const settings = ref({
  errorRateThreshold: 5,
  latencyThreshold: 3000,
  sampleRate: 1,
  retentionDays: 30,
  notifyEmail: true,
  notifyWebhook: false,
  webhook: ''
})

function omitQuery(key: string): Record<string, string> {
  const next: Record<string, string> = {}
  for (const [k, v] of Object.entries(route.query)) {
    if (k !== key && typeof v === 'string') next[k] = v
  }
  return next
}

function saveSettings(): void {
  toast('设置已保存', { tone: 'success', description: '本地生效，P12 接后端持久化' })
  settingsOpen.value = false
}
</script>

<template>
  <div class="u-page">
    <AppPageHeader
      title="LLMOps 运维中心"
      subtitle="调用量、延迟、成本与合规的统一监控入口；所有指标都从 traces 表算出来。"
      compact
    >
      <template #actions>
        <AppButton
          variant="secondary"
          size="sm"
          icon="mdi-bell-alert-outline"
          @click="alertsOpen = true"
        >
          告警中心
        </AppButton>
        <AppButton
          variant="secondary"
          size="sm"
          icon="mdi-cog-outline"
          @click="settingsOpen = true"
        >
          LLMOps 设置
        </AppButton>
      </template>
    </AppPageHeader>

    <AppTabNav v-model="activeTab" :items="TABS" variant="underline" class="llmops-tabs" />

    <RouterView />

    <!-- 告警中心 -->
    <AppModal
      v-model="alertsOpen"
      title="告警中心"
      subtitle="概览页的「最近告警」与成本页的预算提醒，读的都是这张表"
      :max-width="700"
    >
      <p v-if="alertsLoading" class="alerts__loading">加载中…</p>
      <div v-else-if="alerts.length" class="alerts">
        <div v-for="alert in alerts" :key="alert.id" class="alert-item">
          <AppStatusBadge :status="alert.severity" variant="soft" />
          <div class="alert-item__body">
            <p class="alert-item__title">{{ alert.title }}</p>
            <p class="alert-item__detail">{{ alert.detail }}</p>
            <p class="alert-item__meta">
              {{ alert.source }} · {{ formatDateTime(alert.created_at) }}
            </p>
          </div>
          <AppButton
            v-if="alert.status === '未处理'"
            size="sm"
            variant="secondary"
            @click="resolve(alert)"
          >
            标记解决
          </AppButton>
          <AppTagChip v-else label="已解决" tone="success" />
        </div>
      </div>
      <p v-else class="alerts__loading">没有告警，一切正常。</p>

      <template #footer>
        <AppButton variant="secondary" size="sm" @click="alertsOpen = false">关闭</AppButton>
      </template>
    </AppModal>

    <!-- LLMOps 设置 -->
    <AppModal
      v-model="settingsOpen"
      title="LLMOps 设置"
      subtitle="阈值与采样策略；原型是弹窗，内容为补全"
      :max-width="560"
    >
      <div class="settings">
        <AppSlider
          v-model="settings.errorRateThreshold"
          label="错误率告警阈值"
          :min="0"
          :max="20"
          :step="0.5"
          suffix="%"
        />
        <AppSlider
          v-model="settings.latencyThreshold"
          label="平均延迟告警阈值"
          :min="500"
          :max="8000"
          :step="100"
          suffix=" ms"
        />
        <AppSlider
          v-model="settings.sampleRate"
          label="Trace 采样率"
          :min="0.05"
          :max="1"
          :step="0.05"
        />
        <AppSelect
          v-model="settings.retentionDays"
          label="数据保留天数"
          :items="[
            { title: '7 天', value: 7 },
            { title: '30 天', value: 30 },
            { title: '90 天', value: 90 }
          ]"
        />
        <AppSwitch v-model="settings.notifyEmail" label="邮件通知" description="发给 Admin 账号邮箱" show-state />
        <AppSwitch v-model="settings.notifyWebhook" label="Webhook 通知" description="推送到企业微信/飞书" show-state />
        <AppTextarea
          v-if="settings.notifyWebhook"
          v-model="settings.webhook"
          label="Webhook 地址"
          :rows="2"
          placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
        />
      </div>
      <template #footer>
        <AppButton variant="secondary" size="sm" @click="settingsOpen = false">取消</AppButton>
        <AppButton size="sm" @click="saveSettings">保存</AppButton>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.llmops-tabs {
  margin-bottom: var(--spacing-4);
}

.alerts {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border: var(--border-width) solid var(--color-divider);
  border-radius: var(--radius-sm);
}

.alert-item__body {
  flex: 1 1 auto;
  min-width: 0;
}

.alert-item__title {
  font: var(--font-body-md);
  font-weight: 500;
  color: var(--color-text);
}

.alert-item__detail {
  margin-top: 2px;
  font: var(--font-body-sm);
  color: var(--color-text-secondary);
}

.alert-item__meta {
  margin-top: 4px;
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.alerts__loading {
  padding: var(--spacing-6);
  text-align: center;
  font: var(--font-body-sm);
  color: var(--color-text-tertiary);
}

.settings {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}
</style>
