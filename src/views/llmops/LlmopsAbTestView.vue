<script setup lang="ts">
import { ref } from 'vue'
import {
  AppButton,
  AppContentCard,
  AppDataTable,
  AppModal,
  AppSelect,
  AppStatusBadge,
  AppTextField
} from '@/components/ui'
import type { TableColumn } from '@/components/ui'
import { getAbTests } from '@/api/llmops'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'
import { formatDateTime } from '@/utils/format'

/**
 * A/B 测试（原型 08-LLM-AB测试.png）。
 * 后端只有 GET /ab-tests，没有创建接口 —— 弹窗提交先只提示，P12 补 POST。
 */
const { data: rows, loading, reload } = useResource(getAbTests)

const columns: TableColumn[] = [
  { key: 'name', title: '实验名称', width: '26%', emphasis: true, ellipsis: true },
  { key: 'model_a', title: '对照组', width: '16%', render: 'mono' },
  { key: 'model_b', title: '实验组', width: '16%', render: 'mono' },
  { key: 'status', title: '状态', width: '10%', render: 'badge' },
  { key: 'sample_size', title: '样本量', width: '10%', align: 'right', sortable: true },
  { key: 'winner', title: '胜出', width: '12%' },
  { key: 'started_at', title: '开始时间', width: '14%' }
]

const createOpen = ref(false)
const draft = ref({ name: '', modelA: 'gpt-4o', modelB: 'claude-3-5-sonnet', target: 1000 })

function submit(): void {
  if (!draft.value.name.trim()) {
    toast('请填写实验名称', { tone: 'warning' })
    return
  }
  toast('创建接口在 P12 接入', {
    tone: 'info',
    description: `${draft.value.name} · ${draft.value.modelA} vs ${draft.value.modelB}`
  })
  createOpen.value = false
  draft.value.name = ''
}
</script>

<template>
  <AppContentCard title="A/B 测试" subtitle="对照组与实验组按同一批输入跑，比较成功率与延迟" flush>
    <template #actions>
      <AppButton size="sm" icon="mdi-plus" @click="createOpen = true">创建新测试</AppButton>
      <AppButton size="sm" variant="ghost" icon="mdi-refresh" :loading="loading" @click="reload">
        刷新
      </AppButton>
    </template>

    <AppDataTable
      :columns="columns"
      :rows="rows ?? []"
      :loading="loading"
      empty-title="还没有 A/B 测试"
      empty-description="创建一次实验，比较两个模型在同一批输入上的表现"
    >
      <template #cell-winner="{ row }">
        <AppStatusBadge
          v-if="row.winner"
          :status="String(row.winner)"
          tone="success"
          variant="soft"
        />
        <span v-else class="ab-empty">—</span>
      </template>
      <template #cell-started_at="{ row }">
        {{ formatDateTime(row.started_at as string) }}
      </template>
    </AppDataTable>

    <template #footer>
      <span class="ab-foot">共 {{ rows?.length ?? 0 }} 个实验；胜出模型会被标记为推荐配置</span>
    </template>
  </AppContentCard>

  <AppModal v-model="createOpen" title="创建 A/B 测试" subtitle="同一批输入分别打给两个模型" :max-width="520">
    <div class="ab-form">
      <AppTextField v-model="draft.name" label="实验名称" required placeholder="如：摘要提示词 v3 对比" />
      <AppSelect
        v-model="draft.modelA"
        label="对照组模型"
        :items="['gpt-4o', 'gpt-4o-mini', 'claude-3-5-sonnet', 'deepseek-chat']"
      />
      <AppSelect
        v-model="draft.modelB"
        label="实验组模型"
        :items="['gpt-4o', 'gpt-4o-mini', 'claude-3-5-sonnet', 'deepseek-chat']"
      />
      <AppTextField v-model.number="draft.target" label="目标样本量" type="number" />
    </div>
    <template #footer>
      <AppButton variant="secondary" size="sm" @click="createOpen = false">取消</AppButton>
      <AppButton size="sm" @click="submit">创建</AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
.ab-empty {
  color: var(--color-text-tertiary);
}

.ab-foot {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.ab-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}
</style>
