<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  AppButton,
  AppEmptyState,
  AppFilterBar,
  AppPageHeader,
  AppSelect,
  AppTagChip,
  AppTextField
} from '@/components/ui'
import { pluginsApi } from '@/api/resources'
import type { PluginDto } from '@/api/types'
import { useListQuery } from '@/composables/useListQuery'
import { toast } from '@/composables/useToast'

/**
 * 插件市场（原型 09-插件市场.png）。
 * 数据来自后端 plugins 表；「安装」是真的 PATCH installed 字段。
 * 原型没有插件详情页，卡片上也没有详情入口 —— 这里保持一致，安装即止。
 */
const { rows, keyword, loading, error, reload } = useListQuery<PluginDto>((query) =>
  pluginsApi.list({ ...query, size: 50 })
)

const CATEGORY_ICONS: Record<string, string> = {
  搜索: 'mdi-magnify',
  工具: 'mdi-wrench-outline',
  数据: 'mdi-database-outline',
  文档: 'mdi-file-document-outline',
  多媒体: 'mdi-image-multiple-outline',
  办公: 'mdi-briefcase-outline',
  生活: 'mdi-weather-sunny'
}

const category = ref<string>('全部')
const sortBy = ref<'popular' | 'rating' | 'name'>('popular')
const installing = ref<string | null>(null)

const sortOptions = [
  { title: '下载最多', value: 'popular' },
  { title: '评分最高', value: 'rating' },
  { title: '名称', value: 'name' }
]

/** 分类 chips 从数据里长出来，而不是手写一份会过时的常量 */
const categories = computed(() => {
  const set = new Set(rows.value.map((item) => item.category))
  return ['全部', ...[...set].sort()]
})

const visible = computed<PluginDto[]>(() => {
  let list = rows.value.filter((item) => category.value === '全部' || item.category === category.value)
  if (sortBy.value === 'rating') list = [...list].sort((a, b) => b.rating - a.rating)
  else if (sortBy.value === 'name') list = [...list].sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
  else list = [...list].sort((a, b) => b.download_count - a.download_count)
  return list
})

const filtered = computed(() => Boolean(keyword.value.trim()) || category.value !== '全部')

async function install(plugin: PluginDto): Promise<void> {
  if (plugin.installed) {
    toast('已安装', { description: `${plugin.name} 可以在节点里直接选用`, tone: 'info' })
    return
  }
  installing.value = plugin.id
  try {
    await pluginsApi.update(plugin.id, { installed: true })
    toast('安装成功', { description: `${plugin.name} 已加入可用插件` })
    await reload()
  } catch (cause) {
    toast('安装失败', { tone: 'error', description: String(cause) })
  } finally {
    installing.value = null
  }
}

function iconOf(plugin: PluginDto): string {
  return CATEGORY_ICONS[plugin.category] ?? 'mdi-puzzle-outline'
}

function resetFilters(): void {
  keyword.value = ''
  category.value = '全部'
  sortBy.value = 'popular'
}
</script>

<template>
  <div class="u-page">
    <AppPageHeader
      title="插件市场"
      subtitle="安装插件后，Agent 与工作流节点可以直接调用它们提供的能力。"
      compact
    />

    <AppFilterBar :summary="`共 ${visible.length} 个插件`" class="plugin__filter">
      <AppTextField
        v-model="keyword"
        dense
        type="search"
        prefix-icon="mdi-magnify"
        placeholder="搜索插件…"
      />
      <AppTagChip
        v-for="item in categories"
        :key="item"
        :label="item"
        clickable
        :active="item === category"
        @click="category = item"
      />
      <template #actions>
        <AppSelect v-model="sortBy" dense :items="sortOptions" class="plugin__sort" />
        <AppButton size="sm" variant="ghost" icon="mdi-filter-remove-outline" @click="resetFilters">
          重置
        </AppButton>
      </template>
    </AppFilterBar>

    <p v-if="error" class="u-page__error">{{ error }}</p>

    <div v-if="loading" class="plugin__grid">
      <div v-for="i in 8" :key="i" class="plugin-card plugin-card--skeleton">
        <span class="u-skeleton" style="width: 60%" />
        <span class="u-skeleton" style="width: 90%" />
        <span class="u-skeleton" style="width: 40%" />
      </div>
    </div>

    <div v-else-if="visible.length" class="plugin__grid">
      <article v-for="plugin in visible" :key="plugin.id" class="plugin-card">
        <header class="plugin-card__head">
          <span class="plugin-card__icon">
            <i :class="['mdi', iconOf(plugin)]" aria-hidden="true" />
          </span>
          <div class="plugin-card__title">
            <h3 class="plugin-card__name">
              {{ plugin.name }}
              <i
                v-if="plugin.verified"
                class="mdi mdi-check-decagram plugin-card__verified"
                title="官方认证"
                aria-hidden="true"
              />
            </h3>
            <span class="plugin-card__author">{{ plugin.author }}</span>
          </div>
          <AppTagChip v-if="plugin.hot" label="HOT" tone="danger" />
          <AppTagChip :label="plugin.category" />
        </header>

        <p class="plugin-card__desc">{{ plugin.description }}</p>

        <div class="plugin-card__meta">
          <span class="plugin-card__rating">
            <i class="mdi mdi-star" aria-hidden="true" />
            {{ plugin.rating.toFixed(1) }}
          </span>
          <span class="plugin-card__downloads">
            <i class="mdi mdi-download" aria-hidden="true" />
            {{ plugin.download_count.toLocaleString('zh-CN') }}
          </span>
          <span class="plugin-card__price" :class="{ 'is-free': plugin.price === '免费' }">
            {{ plugin.price }}
          </span>
        </div>

        <AppButton
          size="sm"
          :variant="plugin.installed ? 'secondary' : 'primary'"
          :icon="plugin.installed ? 'mdi-check' : 'mdi-download'"
          :loading="installing === plugin.id"
          class="plugin-card__install"
          @click="install(plugin)"
        >
          {{ plugin.installed ? '已安装' : '安装' }}
        </AppButton>
      </article>
    </div>

    <AppEmptyState
      v-else
      icon="mdi-puzzle-outline"
      :title="filtered ? '没有匹配的插件' : '插件市场还是空的'"
      :description="filtered ? '试试换个关键字，或清空分类筛选' : '等后端灌入插件数据'"
    >
      <template #action>
        <AppButton v-if="filtered" size="sm" variant="secondary" @click="resetFilters">
          清空筛选
        </AppButton>
      </template>
    </AppEmptyState>
  </div>
</template>

<style scoped>
.plugin__filter {
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-4);
  flex-wrap: wrap;
}

.plugin__sort {
  width: 130px;
}

.plugin__grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-4);
  padding-bottom: var(--spacing-6);
}

@media (max-width: 1400px) {
  .plugin__grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.plugin-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  background: var(--color-surface);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-md);
}

.plugin-card--skeleton {
  min-height: 180px;
}

.plugin-card__head {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
}

.plugin-card__icon {
  flex: 0 0 auto;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-container);
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.plugin-card__title {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.plugin-card__name {
  display: flex;
  align-items: center;
  gap: 4px;
  font: var(--font-body-md);
  font-weight: 500;
  color: var(--color-text);
}

.plugin-card__verified {
  font-size: 14px;
  color: var(--status-info);
}

.plugin-card__author {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.plugin-card__desc {
  font: var(--font-body-sm);
  color: var(--color-text-secondary);
  line-height: 20px;
  flex: 1 1 auto;
  min-height: 40px;
}

.plugin-card__meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.plugin-card__rating,
.plugin-card__downloads {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.plugin-card__rating .mdi {
  color: #f5a623;
  font-size: 14px;
}

.plugin-card__downloads .mdi {
  font-size: 14px;
}

.plugin-card__price {
  margin-left: auto;
  padding: 1px 8px;
  border-radius: var(--radius-full);
  background: var(--status-warning-bg);
  color: #9a4d00;
}

.plugin-card__price.is-free {
  background: var(--status-success-bg);
  color: var(--status-success);
}

.plugin-card__install {
  width: 100%;
  justify-content: center;
}
</style>
