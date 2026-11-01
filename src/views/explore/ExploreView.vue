<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  AppButton,
  AppEmptyState,
  AppFilterBar,
  AppPageHeader,
  AppSelect,
  AppStatCard,
  AppTagChip,
  AppTextField
} from '@/components/ui'
import { toast } from '@/composables/useToast'
import { useFavorites } from '@/composables/useFavorites'
import {
  EXPLORE_CATEGORIES,
  EXPLORE_TEMPLATES,
  templateTargetPath,
  type TemplateCard
} from './templateCatalog'

/**
 * 探索 AI 模板（原型 02-探索.png）。
 *
 * 4 个统计卡的数字都是算出来的，不是写死的：
 * 总模板数 = 目录长度（16）、热门 = hot 标记数、收藏 = localStorage 里的数量、
 * 总使用次数 = usageCount 求和。
 */
const router = useRouter()
const { count: favoriteCount, isFavorite, toggle } = useFavorites()

const keyword = ref('')
const category = ref<string>('全部')
const sortBy = ref<'popular' | 'rating' | 'newest'>('popular')

const sortOptions = [
  { title: '热门度', value: 'popular' },
  { title: '评分最高', value: 'rating' },
  { title: '最新上架', value: 'newest' }
]

const stats = computed(() => ({
  total: EXPLORE_TEMPLATES.length,
  hot: EXPLORE_TEMPLATES.filter((item) => item.hot).length,
  favorites: favoriteCount.value,
  usage: EXPLORE_TEMPLATES.reduce((sum, item) => sum + item.usageCount, 0)
}))

const visible = computed<TemplateCard[]>(() => {
  const keywordValue = keyword.value.trim().toLowerCase()
  let list = EXPLORE_TEMPLATES.filter((item) => {
    const matchCategory = category.value === '全部' || item.category === category.value
    const matchKeyword =
      !keywordValue ||
      item.name.toLowerCase().includes(keywordValue) ||
      item.description.toLowerCase().includes(keywordValue)
    return matchCategory && matchKeyword
  })

  if (sortBy.value === 'rating') list = [...list].sort((a, b) => b.rating - a.rating)
  else if (sortBy.value === 'newest') list = [...list].sort((a, b) => b.addedAt.localeCompare(a.addedAt))
  else list = [...list].sort((a, b) => b.usageCount - a.usageCount)

  return list
})

const filtered = computed(() => Boolean(keyword.value.trim()) || category.value !== '全部')

function useTemplateTemplate(template: TemplateCard): void {
  void router.push(templateTargetPath(template))
}

function onToggleFavorite(template: TemplateCard): void {
  const added = toggle(template.key)
  toast(added ? '已收藏' : '已取消收藏', { description: template.name, tone: added ? 'success' : 'info' })
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
      title="探索 AI 模板"
      subtitle="发现并使用各种 AI 模板，快速构建您的智能应用，从对话机器人到数据分析，应有尽有。"
      compact
    />

    <div class="explore__stats">
      <AppStatCard icon="mdi-view-grid-outline" :value="stats.total" label="总模板数" tone="accent" />
      <AppStatCard icon="mdi-fire" :value="stats.hot" label="热门模板" tone="warning" />
      <AppStatCard icon="mdi-star-outline" :value="stats.favorites" label="收藏模板" tone="accent" />
      <AppStatCard icon="mdi-chart-line" :value="stats.usage" label="总使用次数" tone="success" />
    </div>

    <AppFilterBar :summary="`共 ${visible.length} 个模板`" class="explore__filter">
      <AppTextField
        v-model="keyword"
        dense
        type="search"
        prefix-icon="mdi-magnify"
        placeholder="搜索模板…"
      />
      <template #actions>
        <AppSelect v-model="sortBy" dense :items="sortOptions" class="explore__sort" />
        <AppButton size="sm" variant="ghost" icon="mdi-filter-remove-outline" @click="resetFilters">
          重置
        </AppButton>
      </template>
    </AppFilterBar>

    <div class="explore__chips">
      <AppTagChip
        v-for="item in EXPLORE_CATEGORIES"
        :key="item"
        :label="item"
        clickable
        :active="item === category"
        @click="category = item"
      />
    </div>
    <div v-if="visible.length" class="explore__grid">
      <article v-for="template in visible" :key="template.key" class="tpl-card">
        <AppTagChip v-if="template.hot" label="HOT" tone="danger" class="tpl-card__hot" />
        <div class="tpl-card__media">
          <span class="tpl-card__icon">
            <i :class="['mdi', template.icon]" aria-hidden="true" />
          </span>

          <button
            type="button"
            class="tpl-card__fav"
            :class="{ 'is-active': isFavorite(template.key) }"
            :aria-label="isFavorite(template.key) ? '取消收藏' : '收藏'"
            @click="onToggleFavorite(template)"
          >
            <i
              :class="['mdi', isFavorite(template.key) ? 'mdi-heart' : 'mdi-heart-outline']"
              aria-hidden="true"
            />
          </button>
        </div>

        <div class="tpl-card__body">
          <AppTagChip :label="template.category" />
          <h3 class="tpl-card__name">{{ template.name }}</h3>
          <p class="tpl-card__desc">{{ template.description }}</p>
          <div class="tpl-card__meta">
            <span class="tpl-card__rating">
              <i class="mdi mdi-star" aria-hidden="true" />
              {{ template.rating.toFixed(1) }}
            </span>
            <span class="tpl-card__usage">
              <i class="mdi mdi-eye-outline" aria-hidden="true" />
              {{ template.usageCount.toLocaleString('zh-CN') }}
            </span>
          </div>
        </div>

        <AppButton
          size="sm"
          variant="secondary"
          icon="mdi-play-circle-outline"
          class="tpl-card__use"
          @click="useTemplateTemplate(template)"
        >
          使用模板
        </AppButton>
      </article>
    </div>

    <AppEmptyState
      v-else
      :icon="filtered ? 'mdi-magnify-close' : 'mdi-view-grid-outline'"
      :title="filtered ? '没有匹配的模板' : '模板目录是空的'"
      :description="filtered ? '试试换个关键字，或清空分类筛选' : '检查 templateCatalog.ts 是否被清空'"
    >
      <template #action>
        <AppButton v-if="filtered" size="sm" variant="secondary" @click="resetFilters">清空筛选</AppButton>
      </template>
    </AppEmptyState>
  </div>
</template>

<style scoped>
.explore__stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-4);
}

@media (max-width: 1280px) {
  .explore__stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.explore__filter {
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-4);
  flex-wrap: wrap;
}

.explore__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-4);
}

.explore__sort {
  width: 130px;
}

.explore__grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-4);
  padding-bottom: var(--spacing-6);
}

@media (max-width: 1400px) {
  .explore__grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.tpl-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  background: var(--color-surface);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-md);
  transition: border-color var(--motion-fast) var(--motion-ease);
}

.tpl-card:hover {
  border-color: var(--color-primary-light);
}

.tpl-card__media {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tpl-card__icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-container);
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.tpl-card__hot {
  position: absolute;
  left: var(--spacing-4);
  top: -11px;
  z-index: 1;
}

.tpl-card__fav {
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: 16px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition:
    background-color var(--motion-fast) var(--motion-ease),
    color var(--motion-fast) var(--motion-ease);
}

.tpl-card__fav:hover {
  background: var(--color-surface-container);
}

.tpl-card__fav.is-active {
  color: #e53935;
}

.tpl-card__body :deep(.tag-chip) {
  align-self: flex-start;
}

.tpl-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  flex: 1 1 auto;
}

.tpl-card__name {
  font: var(--font-title-md);
  color: var(--color-text);
}

.tpl-card__desc {
  font: var(--font-body-sm);
  color: var(--color-text-secondary);
  line-height: 20px;
  min-height: 60px;
}

.tpl-card__meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.tpl-card__rating,
.tpl-card__usage {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tpl-card__rating .mdi {
  color: #f5a623;
  font-size: 14px;
}

.tpl-card__usage .mdi {
  font-size: 14px;
}

.tpl-card__use {
  width: 100%;
  justify-content: center;
}
</style>
