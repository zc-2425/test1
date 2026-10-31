<script setup lang="ts">
import { ref } from 'vue'

/**
 * 标签录入：工作流创建弹窗的「功能标签」、插件分类、Agent 能力标签。
 * 回车或逗号提交，退格删最后一个，重复自动忽略。
 */
const model = defineModel<string[]>({ default: () => [] })

const props = withDefaults(
  defineProps<{
    label?: string
    placeholder?: string
    hint?: string
    max?: number
    disabled?: boolean
  }>(),
  { placeholder: '输入后按回车添加', max: 10 }
)

const draft = ref('')
const inputRef = ref<HTMLInputElement | null>(null)

function add(raw?: string): void {
  const value = (raw ?? draft.value).trim().replace(/,$/, '')
  if (!value) return
  if (model.value.includes(value)) {
    draft.value = ''
    return
  }
  if (model.value.length >= props.max) return
  model.value = [...model.value, value]
  draft.value = ''
}

function remove(index: number): void {
  model.value = model.value.filter((_, i) => i !== index)
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter' || event.key === ',' || event.key === '，') {
    event.preventDefault()
    add()
  } else if (event.key === 'Backspace' && !draft.value && model.value.length) {
    remove(model.value.length - 1)
  }
}

function onPaste(event: ClipboardEvent): void {
  const text = event.clipboardData?.getData('text') ?? ''
  if (!/[,，\n]/.test(text)) return
  event.preventDefault()
  text
    .split(/[,，\n]/)
    .map((part) => part.trim())
    .filter(Boolean)
    .forEach((part) => add(part))
}
</script>

<template>
  <div class="tag-input" :class="{ 'is-disabled': disabled }">
    <label v-if="label" class="tag-input__label">{{ label }}</label>
    <div class="tag-input__box" @click="inputRef?.focus()">
      <span v-for="(tag, index) in model" :key="tag" class="tag-input__chip">
        {{ tag }}
        <button
          v-if="!disabled"
          type="button"
          class="tag-input__remove"
          :aria-label="`移除 ${tag}`"
          @click.stop="remove(index)"
        >
          <i class="mdi mdi-close" aria-hidden="true" />
        </button>
      </span>
      <input
        ref="inputRef"
        v-model="draft"
        class="tag-input__input"
        type="text"
        :placeholder="model.length ? '' : placeholder"
        :disabled="disabled || model.length >= max"
        @keydown="onKeydown"
        @blur="add()"
        @paste="onPaste"
      />
    </div>
    <span class="tag-input__hint">
      {{ hint || `最多 ${max} 个标签，回车或逗号分隔` }}
    </span>
  </div>
</template>

<style scoped>
.tag-input {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.tag-input.is-disabled {
  opacity: 0.6;
}

.tag-input__label {
  font-size: 12px;
  line-height: 16px;
  color: var(--color-text-secondary);
}

.tag-input__box {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  min-height: 40px;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  cursor: text;
  transition: border-color var(--motion-fast) var(--motion-ease);
}

.tag-input__box:focus-within {
  border-color: var(--color-primary);
  box-shadow: inset 0 0 0 1px var(--color-primary);
}

.tag-input__chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  height: 22px;
  padding: 0 4px 0 8px;
  border-radius: var(--radius-full);
  background: var(--color-primary-container);
  color: var(--color-primary);
  font-size: 12px;
  white-space: nowrap;
}

.tag-input__remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: inherit;
  font-size: 12px;
  cursor: pointer;
  opacity: 0.7;
}

.tag-input__remove:hover {
  opacity: 1;
  background: rgba(103, 80, 164, 0.16);
}

.tag-input__input {
  flex: 1 1 80px;
  min-width: 80px;
  height: 24px;
  border: 0;
  outline: none;
  background: transparent;
  font-family: inherit;
  font-size: 13px;
  color: var(--color-text);
}

.tag-input__hint {
  font-size: 12px;
  line-height: 16px;
  color: var(--color-text-tertiary);
}
</style>
