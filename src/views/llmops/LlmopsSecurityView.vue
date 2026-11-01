<script setup lang="ts">
import { computed, reactive } from 'vue'
import {
  AppButton,
  AppContentCard,
  AppProgressInline,
  AppStatusBadge,
  AppSwitch
} from '@/components/ui'
import { getModelPerf, getOverview } from '@/api/llmops'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'
import { formatNumber } from '@/utils/format'

/**
 * 安全合规（原型 08-LLM-安全合规.png，录屏只扫到 Tab 头，内容未知）。
 *
 * 这里只用**真实数据**能算出来的指标（错误率、失败调用、未处理告警），
 * 不编造审计日志 —— 后端还没有审计表，与其放假数据不如把「还没有」说清楚。
 * 合规检查清单是配置项而非统计值，静态列出是合理的。
 */
const { data: overview } = useResource(getOverview)
const { data: perf } = useResource(getModelPerf)

const failureRate = computed(() => {
  const rate = overview.value?.cards.successRate ?? 100
  return Number((100 - rate).toFixed(1))
})

const failedCalls = computed(() => {
  const list = perf.value ?? []
  return list.reduce((sum, row) => sum + Math.round(row.calls * (1 - row.successRate / 100)), 0)
})

const checks = computed(() => [
  {
    key: 'errorRate',
    label: '调用错误率',
    value: `${failureRate.value}%`,
    percent: Math.min(100, failureRate.value * 10),
    tone: failureRate.value > 5 ? 'danger' : 'success',
    hint: '阈值 5%，超过会在告警中心产生一条'
  },
  {
    key: 'alerts',
    label: '未处理告警',
    value: `${overview.value?.cards.activeAlerts ?? 0} 条`,
    percent: Math.min(100, (overview.value?.cards.activeAlerts ?? 0) * 25),
    tone: (overview.value?.cards.activeAlerts ?? 0) > 0 ? 'warning' : 'success',
    hint: '在告警中心里标记解决后会实时减少'
  },
  {
    key: 'failed',
    label: '失败调用数',
    value: `${formatNumber(failedCalls.value)} 次`,
    percent: Math.min(100, failedCalls.value / 2),
    tone: failedCalls.value > 30 ? 'danger' : 'success',
    hint: '按每个模型的 (1 - 成功率) × 调用次数 估算'
  }
])

const checklist = reactive([
  { key: 'pii', label: 'PII 脱敏', desc: '手机号、身份证在入库前脱敏', done: true },
  { key: 'audit', label: '审计日志', desc: '记录谁在什么时候调用了哪个模型', done: false },
  { key: 'quota', label: '配额与限流', desc: '按 key 限制 QPS 与日额度', done: true },
  { key: 'retention', label: '数据保留策略', desc: '对话内容按 30 天自动清理', done: false }
])

const settings = reactive({
  contentModeration: true,
  sensitiveWords: true,
  piiMasking: true,
  auditLog: false
})

function saveSettings(): void {
  toast('安全设置已保存', { tone: 'success', description: '本地生效，P12 接后端持久化' })
}
</script>

<template>
  <div class="security">
    <AppContentCard title="安全监控" subtitle="数据来自 traces 与告警表，没有一个是写死的">
      <div class="checks">
        <div v-for="check in checks" :key="check.key" class="check">
          <div class="check__head">
            <span class="check__label">{{ check.label }}</span>
            <span class="check__value">{{ check.value }}</span>
          </div>
          <AppProgressInline
            :value="check.percent"
            :width="220"
            :show-label="false"
            :tone="check.tone === 'success' ? 'success' : check.tone === 'warning' ? 'warning' : 'danger'"
          />
          <p class="check__hint">{{ check.hint }}</p>
        </div>
      </div>
    </AppContentCard>

    <AppContentCard title="合规检查" subtitle="配置项清单，不是统计值">
      <ul class="checklist">
        <li v-for="item in checklist" :key="item.key" class="checklist__item">
          <i
            :class="['mdi', item.done ? 'mdi-check-circle' : 'mdi-alert-circle-outline']"
            :style="{ color: item.done ? 'var(--status-success)' : 'var(--status-warning)' }"
            aria-hidden="true"
          />
          <div class="checklist__body">
            <span class="checklist__label">{{ item.label }}</span>
            <span class="checklist__desc">{{ item.desc }}</span>
          </div>
          <AppStatusBadge :status="item.done ? '已完成' : '待处理'" variant="soft" />
        </li>
      </ul>
    </AppContentCard>

    <AppContentCard title="安全设置" subtitle="本地状态，P12 接后端" dense>
      <div class="settings">
        <AppSwitch
          v-model="settings.contentModeration"
          label="内容审核"
          description="输出前经过一次安全模型检查"
          show-state
        />
        <AppSwitch
          v-model="settings.sensitiveWords"
          label="敏感词过滤"
          description="命中即拦截并记录"
          show-state
        />
        <AppSwitch
          v-model="settings.piiMasking"
          label="PII 脱敏"
          description="手机号、邮箱、身份证在日志里打码"
          show-state
        />
        <AppSwitch
          v-model="settings.auditLog"
          label="审计日志"
          description="开启后需要建审计表（当前未建）"
          show-state
        />
      </div>
      <template #footer>
        <div class="settings__foot">
          <AppButton size="sm" variant="secondary" @click="saveSettings">保存设置</AppButton>
        </div>
      </template>
    </AppContentCard>
  </div>
</template>

<style scoped>
.security {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  padding-bottom: var(--spacing-6);
  max-width: 1000px;
}

.checks {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-4);
}

@media (max-width: 1280px) {
  .checks {
    grid-template-columns: minmax(0, 1fr);
  }
}

.check {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
  border: var(--border-width) solid var(--color-divider);
  border-radius: var(--radius-sm);
}

.check__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--spacing-2);
}

.check__label {
  font: var(--font-label-sm);
  color: var(--color-text-secondary);
}

.check__value {
  font: var(--font-title-md);
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.check__hint {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  line-height: 18px;
}

.checklist {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.checklist__item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border: var(--border-width) solid var(--color-divider);
  border-radius: var(--radius-sm);
}

.checklist__item .mdi {
  font-size: 18px;
}

.checklist__body {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.checklist__label {
  font: var(--font-body-md);
  color: var(--color-text);
}

.checklist__desc {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.settings {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.settings__foot {
  display: flex;
  justify-content: flex-end;
}
</style>
