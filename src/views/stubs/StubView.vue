<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { SKELETONS } from '@/app/router/skeletons'

const route = useRoute()

const meta = computed(() => route.meta)
const skeleton = computed(() => (meta.value.skeleton ? SKELETONS[meta.value.skeleton] : undefined))
const phase = computed(() => meta.value.phase ?? 'P?')
const fullPath = computed(() => route.fullPath)
const params = computed(() => Object.entries(route.params))
const todos = computed(() => meta.value.todo ?? [])
</script>

<template>
  <div class="stub">
    <header class="stub__header">
      <div class="stub__heading">
        <h1 class="stub__title">{{ meta.title }}</h1>
        <p v-if="meta.subtitle" class="stub__subtitle">{{ meta.subtitle }}</p>
      </div>
      <span class="stub__phase">占位页 · 计划 {{ phase }}</span>
    </header>

    <section class="stub__card">
      <dl class="stub__grid">
        <div class="stub__cell">
          <dt>当前路由</dt>
          <dd class="u-mono">{{ fullPath }}</dd>
        </div>
        <div class="stub__cell">
          <dt>所属模块</dt>
          <dd>{{ meta.module }}</dd>
        </div>
        <div class="stub__cell">
          <dt>页面骨架</dt>
          <dd>{{ skeleton ? `${skeleton.name}（${meta.skeleton}）` : '—' }}</dd>
        </div>
        <div class="stub__cell">
          <dt>对照截图</dt>
          <dd class="u-mono">_ref/{{ meta.screen ?? '—' }}</dd>
        </div>
      </dl>

      <div v-if="params.length" class="stub__params">
        <span class="stub__params-label">路由参数</span>
        <code v-for="[k, v] in params" :key="k" class="stub__code">{{ k }} = {{ v }}</code>
      </div>

      <p v-if="skeleton" class="stub__recipe">
        <i class="mdi mdi-shape-outline" aria-hidden="true" />
        <span>组装顺序：{{ skeleton.recipe }}</span>
      </p>
    </section>

    <section class="stub__card stub__card--todo">
      <h2 class="stub__card-title">本页待实现</h2>
      <ul class="stub__todo">
        <li v-for="(item, i) in todos" :key="i" class="stub__todo-item">
          <i class="mdi mdi-radiobox-blank" aria-hidden="true" />
          <span>{{ item }}</span>
        </li>
        <li v-if="!todos.length" class="stub__todo-empty">尚未登记待办，参见 docs/01-页面清单.md</li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.stub {
  padding: var(--layout-page-padding);
  max-width: var(--layout-content-max);
}

.stub__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-6);
}

.stub__title {
  font: var(--font-headline-sm);
  color: var(--color-text);
}

.stub__subtitle {
  margin-top: var(--spacing-1);
  font: var(--font-body-md);
  color: var(--color-text-secondary);
  max-width: 720px;
}

.stub__phase {
  flex: 0 0 auto;
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  background: var(--color-primary-tint);
  color: var(--color-primary);
  font: var(--font-label-md);
}

.stub__card {
  background: var(--color-surface);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-5);
  margin-bottom: var(--spacing-4);
}

.stub__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--spacing-4);
  margin: 0;
}

.stub__cell dt {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-1);
}

.stub__cell dd {
  margin: 0;
  font: var(--font-body-md);
  color: var(--color-text);
}

.stub__params {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-2);
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: var(--border-width) solid var(--color-divider);
}

.stub__params-label {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.stub__code {
  font-family: var(--font-family-mono);
  font-size: 12px;
  padding: 2px 6px;
  border-radius: var(--radius-xs);
  background: var(--color-surface-low);
  color: var(--color-text-secondary);
}

.stub__recipe {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: var(--border-width) solid var(--color-divider);
  font: var(--font-body-sm);
  color: var(--color-text-secondary);
}

.stub__recipe .mdi {
  color: var(--color-primary);
  font-size: 16px;
  margin-top: 2px;
}

.stub__card-title {
  font: var(--font-title-md);
  color: var(--color-text);
  margin-bottom: var(--spacing-3);
}

.stub__todo {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.stub__todo-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  font: var(--font-body-md);
  color: var(--color-text-secondary);
}

.stub__todo-item .mdi {
  font-size: 14px;
  margin-top: 3px;
  color: var(--color-border);
}

.stub__todo-empty {
  font: var(--font-body-sm);
  color: var(--color-text-tertiary);
}
</style>
